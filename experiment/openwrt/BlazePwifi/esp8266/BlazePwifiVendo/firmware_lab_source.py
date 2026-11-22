#!/usr/bin/env python3
"""Shared C/C++ source extraction helpers for ESP firmware host labs.

The mask preserves Python string indices and newline positions so matches against the
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


def _previous_logical_character_index(source: str, index: int) -> int:
    """Return the prior character after ignoring phase-2 splices before index."""
    cursor = index - 1
    while cursor >= 0:
        if source[cursor] == "\n":
            if (cursor >= 2 and source[cursor - 1] == "\r"
                    and source[cursor - 2] == "\\"):
                cursor -= 3
                continue
            if cursor >= 1 and source[cursor - 1] == "\\":
                cursor -= 2
                continue
        elif source[cursor] == "\r" and cursor >= 1 and source[cursor - 1] == "\\":
            cursor -= 2
            continue
        return cursor
    return -1


def _match_spliced_token(source: str, index: int, token: str):
    """Match one preprocessing token while skipping phase-2 splices between characters."""
    cursor = index
    for offset, expected in enumerate(token):
        if offset:
            cursor = _skip_line_splices(source, cursor)
        if cursor >= len(source) or source[cursor] != expected:
            return None
        cursor += 1
    return cursor


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


def _raw_string_literal_end(source: str, index: int):
    """Return the end of a C++ raw string, including any encoding prefix.

    Phase-2 backslash-newline splices may occur between characters of the
    encoding prefix and the opening quote. Match the logical token while
    retaining physical offsets so the mask still preserves source positions.
    """
    previous = _previous_logical_character_index(source, index)
    if previous >= 0 and (source[previous].isalnum() or source[previous] == "_"):
        return None

    prefixes = ("u8R", "uR", "UR", "LR", "R")
    prefix_end = None
    for prefix in prefixes:
        prefix_end = _match_spliced_token(source, index, prefix + '"')
        if prefix_end is not None:
            break
    if prefix_end is None:
        return None

    delimiter_start = prefix_end
    paren = source.find("(", delimiter_start)
    if paren < 0 or paren - delimiter_start > 16:
        return None

    delimiter = source[delimiter_start:paren]
    if any(ch.isspace() or ch in "\\()"
           for ch in delimiter):
        return None

    terminator = ")" + delimiter + '"'
    end = source.find(terminator, paren + 1)
    if end < 0:
        raise RuntimeError("unterminated C/C++ raw string")
    return end + len(terminator)


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

        raw_end = _raw_string_literal_end(source, index)
        if raw_end is not None:
            blank(index, raw_end)
            index = raw_end
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

def _literal_preprocessor_condition(expression: str):
    """Return a boolean only for literal #if/#elif 0 or 1 conditions."""
    value = expression.strip()
    if value in ("0", "(0)"):
        return False
    if value in ("1", "(1)"):
        return True
    return None


def _logical_preprocessor_lines(source: str):
    """Yield phase-2 logical lines with their original physical source ranges.

    C/C++ removes backslash-newline pairs before recognizing # and %: preprocessing
    directives. Keep the physical range so later masking can preserve every
    original offset and newline without building a full preprocessor.
    """
    start = 0
    index = 0
    logical = []

    while index < len(source):
        if source[index] == "\\" and index + 1 < len(source):
            if source[index + 1] == "\n":
                index += 2
                continue
            if source[index + 1] == "\r":
                index += 2
                if index < len(source) and source[index] == "\n":
                    index += 1
                continue

        if source[index] == "\r":
            end = index + 1
            if end < len(source) and source[end] == "\n":
                end += 1
            yield "".join(logical), start, end
            logical = []
            index = end
            start = end
            continue

        if source[index] == "\n":
            end = index + 1
            yield "".join(logical), start, end
            logical = []
            index = end
            start = end
            continue

        logical.append(source[index])
        index += 1

    if start < len(source) or logical:
        yield "".join(logical), start, len(source)


def _mask_inactive_preprocessor_branches(code_source: str) -> str:
    """Mask branches known inactive from literal #if/#elif 0/1 directives.

    Directive recognition follows C/C++ phase-2 line splicing, including
    splices inside directive keywords and expressions. Unknown macro
    expressions remain conservatively visible; this is not a full C
    preprocessor. The returned mask preserves every source offset and newline.
    """
    masked = list(code_source)
    frames = []
    active = True

    for logical_line, start, end in _logical_preprocessor_lines(code_source):
        directive = re.match(
            r"^[ \t]*(?:#|%:)[ \t]*(if|ifdef|ifndef|elif|else|endif)\b(.*)$",
            logical_line,
        )
        if directive:
            command = directive.group(1)
            expression = directive.group(2).strip()

            if command in ("if", "ifdef", "ifndef"):
                condition = (
                    _literal_preprocessor_condition(expression)
                    if command == "if" else None
                )
                parent_active = active
                frames.append({
                    "parent_active": parent_active,
                    "branch_taken": condition,
                })
                active = parent_active and condition is not False

            elif command == "elif" and frames:
                frame = frames[-1]
                if not frame["parent_active"] or frame["branch_taken"] is True:
                    active = False
                elif frame["branch_taken"] is None:
                    # A preceding unknown macro branch may already be active,
                    # but a literal #elif 0 is still definitely inactive.
                    condition = _literal_preprocessor_condition(expression)
                    active = condition is not False
                else:
                    condition = _literal_preprocessor_condition(expression)
                    active = condition is not False
                    if condition is True:
                        frame["branch_taken"] = True

            elif command == "else" and frames:
                frame = frames[-1]
                active = frame["parent_active"] and frame["branch_taken"] is not True
                frame["branch_taken"] = True

            elif command == "endif" and frames:
                active = frames.pop()["parent_active"]

        elif not active:
            for index in range(start, end):
                if code_source[index] not in "\r\n":
                    masked[index] = " "

    return "".join(masked)

def mask_active_cpp_code(source: str) -> str:
    """Mask comments, literals, and provably inactive literal preprocessor branches.

    Unknown macro expressions remain visible. This is a bounded source-analysis
    helper, not a replacement for the compiler's complete preprocessor.
    The returned text preserves Python string indices and CR/LF positions.
    """
    code_source = mask_non_code(source)
    active_source = _mask_inactive_preprocessor_branches(code_source)
    if len(active_source) != len(source):
        raise RuntimeError("active C++ mask changed source offsets")
    source_newlines = [index for index, char in enumerate(source) if char in "\r\n"]
    active_newlines = [index for index, char in enumerate(active_source) if char in "\r\n"]
    if active_newlines != source_newlines:
        raise RuntimeError("active C++ mask changed newline positions")
    return active_source


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

