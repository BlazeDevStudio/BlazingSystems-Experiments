"""Small C++ lexical normalizer for source-extracted firmware parity labs.

This is deliberately not a complete C++ parser. It preserves the token
boundaries needed by the ESP8266/ESP32 parity check and rejects malformed
comments/literals rather than silently normalizing them.
"""

_CPP_MULTI_CHAR_PUNCTUATORS = tuple(
    sorted(
        (
            "%:%:", ">>=", "<<=", "->*", "...", "<=>", "[[", "]]",
            "++", "--", "->", ".*", "::", "&&", "||", "<=", ">=",
            "==", "!=", "+=", "-=", "*=", "/=", "%=", "^=", "&=",
            "|=", "<<", ">>", "##", "<:", ":>", "<%", "%>", "%:",
        ),
        key=len,
        reverse=True,
    )
)


def _scan_preprocessing_number(source, index):
    """Consume a C++ preprocessing-number token, including exponent signs."""
    start = index
    if source[index] == ".":
        index += 1

    while index < len(source):
        char = source[index]
        if char.isalnum() or char in "_.":
            index += 1
            continue

        if char == "'" and index + 1 < len(source):
            next_char = source[index + 1]
            if next_char.isalnum() or next_char == "_":
                index += 2
                continue

        if char in "+-" and index > start and source[index - 1] in "eEpP":
            index += 1
            continue

        break

    return ("number", source[start:index]), index


def tokenize_cpp(source):
    """Return a conservative C++ token sequence for parity comparisons."""
    tokens = []
    index = 0

    while index < len(source):
        if source[index].isspace():
            index += 1
            continue

        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            while (
                newline >= 0
                and newline > index
                and source[newline - 1] == "\\"
            ):
                newline = source.find("\n", newline + 1)
            index = len(source) if newline < 0 else newline + 1
            continue

        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end < 0:
                raise ValueError("unterminated C++ block comment")
            index = end + 2
            continue

        raw_prefix = next(
            (
                prefix
                for prefix in ("u8R", "uR", "UR", "LR", "R")
                if source.startswith(prefix + '"', index)
            ),
            None,
        )
        if raw_prefix is not None:
            quote_index = index + len(raw_prefix)
            open_paren = source.find("(", quote_index + 1)
            if open_paren < 0:
                raise ValueError("malformed C++ raw string literal")
            delimiter = source[quote_index + 1 : open_paren]
            if (
                len(delimiter) > 16
                or any(
                    char.isspace() or char in "()\\" or ord(char) < 0x20
                    for char in delimiter
                )
            ):
                raise ValueError("invalid C++ raw string delimiter")
            terminator = ")" + delimiter + '"'
            end = source.find(terminator, open_paren + 1)
            if end < 0:
                raise ValueError("unterminated C++ raw string literal")
            end += len(terminator)
            tokens.append(("literal", source[index:end]))
            index = end
            continue

        quote = None
        quote_index = None
        for prefix in ("u8", "u", "U", "L", ""):
            candidate = index + len(prefix)
            if (
                candidate < len(source)
                and source.startswith(prefix, index)
                and source[candidate] in ("'", '"')
            ):
                quote = source[candidate]
                quote_index = candidate
                break
        if quote is not None:
            start = index
            index = quote_index + 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                    continue
                if source[index] == quote:
                    index += 1
                    tokens.append(("literal", source[start:index]))
                    break
                index += 1
            else:
                raise ValueError("unterminated C++ quoted literal")
            continue

        char = source[index]
        if char.isalpha() or char == "_":
            start = index
            index += 1
            while index < len(source) and (
                source[index].isalnum() or source[index] == "_"
            ):
                index += 1
            tokens.append(("identifier", source[start:index]))
            continue

        if char.isdigit() or (
            char == "." and index + 1 < len(source) and source[index + 1].isdigit()
        ):
            token, index = _scan_preprocessing_number(source, index)
            tokens.append(token)
            continue

        punctuator = next(
            (
                item
                for item in _CPP_MULTI_CHAR_PUNCTUATORS
                if source.startswith(item, index)
            ),
            None,
        )
        if punctuator is None:
            tokens.append(("punct", char))
            index += 1
        else:
            tokens.append(("punct", punctuator))
            index += len(punctuator)

    return tuple(tokens)
