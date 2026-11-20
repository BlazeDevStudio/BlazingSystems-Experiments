#!/usr/bin/env python3
"""Shared C/C++ source extraction helpers for ESP firmware host labs.

The mask preserves byte offsets and newline positions so matches against the
masked source can safely slice the original source. Comments, ordinary
literals, and C++ raw strings are ignored when locating blocks and functions.
"""
import re
from pathlib import Path


_FUNCTION_MODIFIERS = r"(?:static|inline|constexpr|IRAM_ATTR|ICACHE_RAM_ATTR)"


def _skip_line_splices(source: str, index: int) -> int:
    """Skip C++ phase-2 backslash-newline pairs starting at index."""
    while index < len(source) and source[index] == "\\":
        if index + 1 < len(source) and source[index + 1] == "\n":
            index += 2
        elif index + 1 < len(source) and source[index + 1] == "\r":
            if index + 2 < len(source) and source[index + 2] == "\n":
                index += 3
            else:
                index += 2
        else:
            break
    return index


def _comment_delimiter_end(
    source: str, index: int, first: str, second: str
):
    """Return the physical end of a two-character comment token.

    C++ phase 2 removes backslash-newline pairs before phase-3 comment
    recognition, so the delimiter characters may not be adjacent in the
    physical source. The returned offset still addresses the original text.
    """
    if index >= len(source) or source[index] != first:
        return None
    second_index = _skip_line_splices(source, index + 1)
    if second_index < len(source) and source[second_index] == second:
        return second_index + 1
    return None


def mask_non_code(source: str) -> str:
    """Blank comments and literals while preserving offsets and line breaks."""
    masked = list(source)

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if source[position] not in "\r\n":
                masked[position] = " "

    index = 0
    while index < len(source):
        line_comment_end = _comment_delimiter_end(source, index, "/", "/")
        if line_comment_end is not None:
            start = index
            index = line_comment_end
            while index < len(source):
                if source[index] not in "\r\n":
                    index += 1
                    continue

                # A backslash-newline inside // continues the comment.
                newline_end = index + 1
                if (source[index] == "\r" and newline_end < len(source)
                        and source[newline_end] == "\n"):
                    newline_end += 1
                if index > start and source[index - 1] == "\\":
                    index = newline_end
                    continue
                break
            blank(start, index)
            continue

        block_comment_end = _comment_delimiter_end(source, index, "/", "*")
        if block_comment_end is not None:
            start = index
            cursor = block_comment_end
            end = None
            while cursor < len(source):
                candidate_end = _comment_delimiter_end(source, cursor, "*", "/")
                if candidate_end is not None:
                    end = candidate_end
                    break
                cursor += 1
            if end is None:
                raise RuntimeError("unterminated C/C++ block comment")
            index = end
            blank(start, index)
            continue

        if source.startswith('R"', index):
            delimiter_start = index + 2
            paren = source.find("(", delimiter_start)
            if paren != -1 and paren - delimiter_start <= 16:
                delimiter = source[delimiter_start:paren]
                if not any(ch.isspace() or ch in "\\()" for ch in delimiter):
                    terminator = ")" + delimiter + '"'
                    end = source.find(terminator, paren + 1)
                    if end < 0:
                        raise RuntimeError("unterminated C/C++ raw string")
                    end += len(terminator)
                    blank(index, end)
                    index = end
                    continue

        if source[index] in ('"', "'"):
            quote = source[index]
            start = index
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    index += 1
                    break
                index += 1
            else:
                raise RuntimeError("unterminated C/C++ string or character literal")
            blank(start, index)
            continue

        index += 1

    return "".join(masked)

def _matching_brace_masked(masked: str, opening: int) -> int:
    """Return the closing brace for an opening brace in masked source."""
    if opening < 0 or opening >= len(masked) or masked[opening] != "{":
        raise ValueError("opening index must point to a code '{'")

    depth = 0
    for index in range(opening, len(masked)):
        if masked[index] == "{":
            depth += 1
        elif masked[index] == "}":
            depth -= 1
            if depth == 0:
                return index

    raise RuntimeError("unbalanced C/C++ block")


def matching_brace(source: str, opening: int) -> int:
    """Return a matching brace while ignoring comments and literal contents."""
    return _matching_brace_masked(mask_non_code(source), opening)


def extract_block(source: str, marker: str) -> str:
    """Extract a marked C/C++ block from its marker through its closing brace."""
    masked = mask_non_code(source)
    start = masked.find(marker)
    if start < 0:
        raise RuntimeError(f"missing source block: {marker}")
    opening = masked.find("{", start)
    if opening < 0:
        raise RuntimeError(f"missing source block opener: {marker}")
    return source[start:_matching_brace_masked(masked, opening) + 1]


def extract_functions(source: str, name: str):
    """Return every actual definition as (source_offset, original_text).

    Declarations, calls, comments, and string decoys are not definitions.
    """
    masked = mask_non_code(source)
    signature = re.compile(
        rf"(?m)^[ \t]*(?:(?:{_FUNCTION_MODIFIERS})\s+)*"
        rf"(?:[A-Za-z_][\w:<>*&]*[ \t]+)+"
        rf"(?:(?:{_FUNCTION_MODIFIERS})\s+)*{re.escape(name)}"
        r"\s*\([^;{}]*\)\s*(?:const\s*)?\{"
    )
    found = []
    position = 0
    while True:
        match = signature.search(masked, position)
        if not match:
            break
        opening = match.end() - 1
        end = _matching_brace_masked(masked, opening)
        found.append((match.start(), source[match.start():end + 1]))
        position = end + 1
    return found


def extract_function(source: str, name: str, required: bool = True) -> str:
    """Return the first definition, or an empty string when optional."""
    found = extract_functions(source, name)
    if not found:
        if required:
            raise RuntimeError(f"missing function definition: {name}")
        return ""
    return found[0][1]

def find_repo_root(start: Path) -> Path:
    """Find the repository root from a file/directory path, independent of CWD.

    Both board sketches are required sentinels so a moved/partial lab checkout
    fails with an explicit diagnostic instead of silently using another folder.
    """
    location = Path(start).expanduser().resolve()
    if not location.is_dir():
        location = location.parent

    required_sketches = (
        Path("experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
        Path("experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
    )
    for candidate in (location, *location.parents):
        if all((candidate / relative).is_file() for relative in required_sketches):
            return candidate

    raise RuntimeError(
        f"could not locate BlazePwifi repository root from {Path(start).resolve()}"
    )

