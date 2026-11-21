"""C++ token-aware normalization for source-exact ESP board parity checks.

Only code whitespace is normalized; literal and comment bytes remain significant.
The self-test cases run from the existing poll-loop lab runner.
"""

def normalize_cpp_function_body(body):
    """Collapse code whitespace without changing C++ literal or comment bytes."""
    output = []
    pending_space = False
    i = 0

    def flush_space():
        nonlocal pending_space
        if pending_space and output and output[-1] != " ":
            output.append(" ")
        pending_space = False

    raw_prefixes = ("u8R\"", "uR\"", "UR\"", "LR\"", "R\"")
    while i < len(body):
        ch = body[i]

        if ch.isspace():
            pending_space = True
            i += 1
            continue

        raw_prefix = next((prefix for prefix in raw_prefixes if body.startswith(prefix, i)), None)
        if raw_prefix is not None:
            flush_space()
            quote_index = i + len(raw_prefix) - 1
            open_paren = body.find("(", quote_index + 1)
            if open_paren < 0:
                raise ValueError("unterminated C++ raw-string delimiter")
            delimiter = body[quote_index + 1:open_paren]
            if len(delimiter) > 16 or any(c.isspace() or c in "()\\" for c in delimiter):
                raise ValueError("invalid C++ raw-string delimiter")
            terminator = ")" + delimiter + '"'
            close = body.find(terminator, open_paren + 1)
            if close < 0:
                raise ValueError("unterminated C++ raw string")
            end = close + len(terminator)
            output.append(body[i:end])
            i = end
            pending_space = False
            continue

        if body.startswith("//", i):
            start = i
            cursor = i + 2
            while cursor < len(body):
                if body[cursor] not in "\r\n":
                    cursor += 1
                    continue
                newline_end = cursor + 1
                if body[cursor] == "\r" and newline_end < len(body) and body[newline_end] == "\n":
                    newline_end += 1
                # C++ phase 2 splices backslash-newline before // comment parsing.
                # Keep every continued physical line inside the comment token.
                if cursor > start and body[cursor - 1] == "\\":
                    cursor = newline_end
                    continue
                break
            end = cursor
            comment = body[start:end].replace("\r\n", "\n").replace("\r", "\n")
            if output and output[-1] != " ":
                output.append(" ")
            output.append(comment)
            i = end
            pending_space = True
            continue

        if body.startswith("/*", i):
            end = body.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated C++ block comment")
            end += 2
            comment = body[i:end].replace("\r\n", "\n").replace("\r", "\n")
            if output and output[-1] != " ":
                output.append(" ")
            output.append(comment)
            i = end
            pending_space = True
            continue

        if ch in ("\"", "'"):
            flush_space()
            quote = ch
            literal_start = i
            i += 1
            while i < len(body):
                if body[i] == "\\":
                    if i + 1 >= len(body):
                        raise ValueError("unterminated C++ escape sequence")
                    i += 2
                elif body[i] == quote:
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError("unterminated C++ quoted literal")
            output.append(body[literal_start:i])
            pending_space = False
            continue

        flush_space()
        output.append(ch)
        i += 1
        pending_space = False

    return "".join(output)


def verify_cpp_parity_normalizer():
    cases = (
        ("formatting-only", 'void f() { return "pending event"; }', 'void f()  {\n  return   "pending event";  }', True),
        ("string-literal-whitespace", 'void f(){ return "pending event"; }', 'void f(){ return "pending  event"; }', False),
        ("character-literal-whitespace", "void f(){ char c=' '; }", r"void f(){ char c='\t'; }", False),
        ("comment-content", "void f(){ /* durable record */ return true; }", "void f(){ /*durable record*/ return true; }", False),
        ("raw-string-literal-whitespace", 'void f(){ auto s=R"tag(pending event)tag"; }', 'void f(){ auto s=R"tag(pending  event)tag"; }', False),
        ("escaped-quote", r'void f(){ const char *s="quote: \" pending"; }', r'void f(){ const char *s="quote: pending"; }', False),
        ("line-comment-content", "void f(){ // pending event\n return true; }", "void f(){ // pending  event\n return true; }", False),
        ("line-comment-backslash-newline-content", "void f(){ // pending \\\n event  text\n return true; }", "void f(){ // pending \\\n event text\n return true; }", False),
        ("line-comment-splice-boundary", "void f(){ // pending \\\n return false;\n}", "void f(){ // pending\n return false;\n}", False),
        ("line-comment-crlf-normalization", "void f(){ // pending \\\r\n event text\r\n return true; }", "void f(){ // pending \\\n event text\n return true; }", True),
        ("preprocessor-directive-line-boundary",
         'void f(){\n#if defined(ESP32)\n return true;\n#endif\n}',
         'void f(){ #if defined(ESP32)\n return true;\n#endif\n}', False),
        ("preprocessor-directive-leading-whitespace",
         'void f(){\n#if defined(ESP32)\n return true;\n#endif\n}',
         'void f(){\n    #if defined(ESP32)\n return true;\n#endif\n}', True),
        ("preprocessor-directive-crlf-normalization",
         '#if FEATURE\r\nint value;\r\n#endif\r\n',
         '#if FEATURE\nint value;\n#endif\n', True),
    )
    for label, left, right, expected_equal in cases:
        actual_equal = normalize_cpp_function_body(left) == normalize_cpp_function_body(right)
        if actual_equal != expected_equal:
            raise SystemExit(f"POLL_SAFETY_CPP_PARITY_NORMALIZER_FAIL: {label}")
    print(f"POLL_SAFETY_CPP_PARITY_NORMALIZER_PASS {len(cases)}/{len(cases)}")
