"""Small shared C/C++ source extractor for PHX Hardware host labs.

Masks comments and literals without changing offsets, then locates real function
definitions and balanced blocks. This is test tooling, not a complete compiler.
"""
import re


_RAW_PREFIXES = ('u8R"', 'uR"', 'UR"', 'LR"', 'R"')


def _raw_string_end(source: str, index: int):
    previous = source[index - 1] if index else ""
    if previous.isalnum() or previous == "_":
        return None
    prefix = next((item for item in _RAW_PREFIXES if source.startswith(item, index)), None)
    if prefix is None:
        return None

    delimiter_start = index + len(prefix)
    paren = source.find("(", delimiter_start)
    if paren < 0 or paren - delimiter_start > 16:
        return None
    delimiter = source[delimiter_start:paren]
    if any(char.isspace() or char in "\\()" for char in delimiter):
        return None

    terminator = ")" + delimiter + '"'
    end = source.find(terminator, paren + 1)
    if end < 0:
        raise AssertionError("unterminated C++ raw string")
    return end + len(terminator)


def mask_non_code(source: str) -> str:
    """Blank comments and literals while preserving offsets and line breaks."""
    masked = list(source)

    def blank(start: int, end: int) -> None:
        for pos in range(start, end):
            if source[pos] not in "\r\n":
                masked[pos] = " "

    index = 0
    while index < len(source):
        if source.startswith("//", index):
            start = index
            index += 2
            while index < len(source):
                if source[index] in "\r\n":
                    if index > start and source[index - 1] == "\\":
                        if source[index] == "\r":
                            index += 1
                            if index < len(source) and source[index] == "\n":
                                index += 1
                        else:
                            index += 1
                        continue
                    break
                index += 1
            blank(start, index)
            continue

        if source.startswith("/*", index):
            start = index
            end = source.find("*/", index + 2)
            if end < 0:
                raise AssertionError("unterminated C++ block comment")
            index = end + 2
            blank(start, index)
            continue

        raw_end = _raw_string_end(source, index)
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
                    index += 1
                    if index < len(source) and source[index] == "\r":
                        index += 1
                        if index < len(source) and source[index] == "\n":
                            index += 1
                    elif index < len(source):
                        index += 1
                    continue
                if source[index] == quote:
                    index += 1
                    break
                index += 1
            else:
                raise AssertionError("unterminated C++ string/character literal")
            blank(start, index)
            continue

        index += 1

    return "".join(masked)


def _matching_brace(masked: str, opening: int) -> int:
    if opening < 0 or opening >= len(masked) or masked[opening] != "{":
        raise AssertionError("opening index must point to a code brace")
    depth = 0
    for pos in range(opening, len(masked)):
        if masked[pos] == "{":
            depth += 1
        elif masked[pos] == "}":
            depth -= 1
            if depth == 0:
                return pos
    raise AssertionError("unbalanced C++ block")


def extract_braced(source: str, brace_at: int) -> str:
    """Return a balanced block from a code opening brace."""
    masked = mask_non_code(source)
    end = _matching_brace(masked, brace_at)
    return source[brace_at:end + 1]


def extract_function(source: str, signature: str) -> str:
    """Extract a real definition identified by an exact signature prefix."""
    masked = mask_non_code(source)
    search_at = 0
    while True:
        start = masked.find(signature, search_at)
        if start < 0:
            raise AssertionError(f"missing function definition: {signature}")

        open_paren = masked.find("(", start)
        if open_paren < 0:
            raise AssertionError(f"missing parameter list: {signature}")
        depth = 0
        close_paren = -1
        for pos in range(open_paren, len(masked)):
            if masked[pos] == "(":
                depth += 1
            elif masked[pos] == ")":
                depth -= 1
                if depth == 0:
                    close_paren = pos
                    break
        if close_paren < 0:
            raise AssertionError(f"unclosed parameter list: {signature}")

        cursor = close_paren + 1
        while cursor < len(masked) and masked[cursor].isspace():
            cursor += 1
        if cursor < len(masked) and masked[cursor] == "{":
            end = _matching_brace(masked, cursor)
            return source[start:end + 1]

        # Skip declarations and other non-definition matches.
        search_at = start + len(signature)


def has_empty_string_assignment(source: str, identifier: str) -> bool:
    """Recognize an actual code assignment to an empty string literal."""
    masked = mask_non_code(source)
    pattern = re.compile(rf"\b{re.escape(identifier)}\s*=")
    for match in pattern.finditer(masked):
        cursor = match.end()
        while cursor < len(source) and source[cursor].isspace():
            cursor += 1
        if source.startswith('""', cursor):
            return True
    return False
