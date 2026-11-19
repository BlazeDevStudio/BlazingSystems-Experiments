#!/usr/bin/env python3
"""Shared C/C++ source extraction helpers for ESP firmware host labs.

The mask preserves byte offsets and newline positions so matches against the
masked source can safely slice the original source. Comments, ordinary
literals, and C++ raw strings are ignored when locating blocks and functions.
"""
import re


_FUNCTION_MODIFIERS = r"(?:static|inline|constexpr|IRAM_ATTR|ICACHE_RAM_ATTR)"


def mask_non_code(source: str) -> str:
    """Blank comments and literals while preserving offsets and line breaks."""
    masked = list(source)

    def blank(start: int, end: int) -> None:
        for position in range(start, end):
            if source[position] not in "\r\n":
                masked[position] = " "

    index = 0
    while index < len(source):
        if source.startswith("//", index):
            start = index
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            blank(start, index)
            continue

        if source.startswith("/*", index):
            start = index
            end = source.find("*/", index + 2)
            if end < 0:
                raise RuntimeError("unterminated C/C++ block comment")
            index = end + 2
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
        rf"(?:[A-Za-z_][\w:<>*&]*[ \t]+)+{re.escape(name)}"
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
