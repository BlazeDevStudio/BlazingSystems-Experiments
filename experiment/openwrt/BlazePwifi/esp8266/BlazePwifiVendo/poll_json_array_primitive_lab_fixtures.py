"""C++ fixture programs and parser symbol lists for the strict poll JSON grammar lab.

Keep test inputs separate from extraction, compilation and mutation orchestration.
These fixtures validate syntax only; they do not authenticate a controller response.
"""

PARSER_FUNCTIONS = (
    "pollJsonSpace",
    "pollJsonHex",
    "pollJsonSkipString",
    "pollJsonSkipPrimitive",
    "pollJsonSkipValueDepth",
    "pollJsonSkipCompositeDepth",
    "pollJsonSkipComposite",
    "pollJsonSkipValue",
    "pollJsonTopLevelTrue",
)

PROTOTYPES = (
    "bool pollJsonSkipValueDepth(const String &r,int &p,uint8_t depth);\n"
    "bool pollJsonSkipCompositeDepth(const String &r,int &p,uint8_t depth);\n"
)

COMPOSITE_MAIN = r"""
int main() {
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"items\":[1,2,3]}"), "ok")) return 61;
  if (!pollJsonTopLevelTrue(
          String("{\"items\":[1,2,3],\"ok\":true}"), "ok")) return 62;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[false,null,-1.25e+2,{\"nested\":[true,0]}]}"),
          "ok")) return 63;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[]}"), "ok")) return 64;
  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{}}"), "ok")) return 65;

  if (!pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"quote\\\" slash\\\\ backspace\\b formfeed\\f newline\\n carriage\\r tab\\t unicode\\u0041\"}"),
          "ok")) return 72;

  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1,]}"), "ok")) return 66;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1 2]}"), "ok")) return 67;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{\"a\":1,}}"), "ok")) return 68;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{\"a\" 1}}"), "ok")) return 69;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":[1,2,3}"), "ok")) return 70;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":{\"a\":1 \"b\":2}}"), "ok")) return 71;

  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\\x41\"}"), "ok")) return 73;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\\u12\"}"), "ok")) return 74;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\\u12G4\"}"), "ok")) return 75;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"bad\nline\"}"), "ok")) return 76;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"unterminated}"), "ok")) return 77;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"meta\":\"dangling\\"), "ok")) return 78;

  std::cout << "POLL_JSON_COMPOSITE_GRAMMAR_PASS valid=6/6 invalid=12/12\n";
  return 0;
}
"""


DUPLICATE_ROOT_MAIN = r"""
int main() {
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"ok\":true}"), "ok")) return 91;
  if (pollJsonTopLevelTrue(
          String("{\"ok\":true,\"ok\":false}"), "ok")) return 92;
  std::cout << "POLL_JSON_DUPLICATE_ROOT_STATUS_DENY_PASS 2/2\n";
  return 0;
}
"""


TRAILING_DATA_MAIN = r"""
int main() {
  if (pollJsonTopLevelTrue(String("{\"ok\":true}trailing"), "ok")) return 93;
  if (pollJsonTopLevelTrue(String("{\"ok\":true}{\"ok\":true}"), "ok")) return 94;
  if (pollJsonTopLevelTrue(String("{\"ok\":true} \n trailing"), "ok")) return 95;
  if (!pollJsonTopLevelTrue(String("{\"ok\":true} \t\r\n"), "ok")) return 96;
  std::cout << "POLL_JSON_TRAILING_DATA_DENY_PASS 3/3 WHITESPACE_ACCEPTED=1\n";
  return 0;
}
"""


PRIMITIVE_MAIN = r"""
int main() {
  if (!pollJsonTopLevelTrue(String("{\"meta\":0,\"ok\":true}"), "ok")) return 81;
  if (!pollJsonTopLevelTrue(String("{\"meta\":-0,\"ok\":true}"), "ok")) return 82;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1,\"ok\":true}"), "ok")) return 83;
  if (!pollJsonTopLevelTrue(String("{\"meta\":-12,\"ok\":true}"), "ok")) return 84;
  if (!pollJsonTopLevelTrue(String("{\"meta\":0.25,\"ok\":true}"), "ok")) return 85;
  if (!pollJsonTopLevelTrue(String("{\"meta\":-0.25,\"ok\":true}"), "ok")) return 86;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1e3,\"ok\":true}"), "ok")) return 87;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1E+3,\"ok\":true}"), "ok")) return 88;
  if (!pollJsonTopLevelTrue(String("{\"meta\":1e-3,\"ok\":true}"), "ok")) return 89;

  if (pollJsonTopLevelTrue(String("{\"meta\":01,\"ok\":true}"), "ok")) return 101;
  if (pollJsonTopLevelTrue(String("{\"meta\":-01,\"ok\":true}"), "ok")) return 102;
  if (pollJsonTopLevelTrue(String("{\"meta\":+1,\"ok\":true}"), "ok")) return 103;
  if (pollJsonTopLevelTrue(String("{\"meta\":.1,\"ok\":true}"), "ok")) return 104;
  if (pollJsonTopLevelTrue(String("{\"meta\":1.,\"ok\":true}"), "ok")) return 105;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e,\"ok\":true}"), "ok")) return 106;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e+,\"ok\":true}"), "ok")) return 107;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e-,\"ok\":true}"), "ok")) return 108;
  if (pollJsonTopLevelTrue(String("{\"meta\":--1,\"ok\":true}"), "ok")) return 109;
  if (pollJsonTopLevelTrue(String("{\"meta\":NaN,\"ok\":true}"), "ok")) return 110;
  if (pollJsonTopLevelTrue(String("{\"meta\":Infinity,\"ok\":true}"), "ok")) return 111;
  if (pollJsonTopLevelTrue(String("{\"meta\":TRUE,\"ok\":true}"), "ok")) return 112;
  if (pollJsonTopLevelTrue(String("{\"meta\":tru,\"ok\":true}"), "ok")) return 113;
  if (pollJsonTopLevelTrue(String("{\"meta\":nullx,\"ok\":true}"), "ok")) return 114;
  if (pollJsonTopLevelTrue(String("{\"meta\":1e++2,\"ok\":true}"), "ok")) return 115;
  if (pollJsonTopLevelTrue(String("{\"meta\":0x10,\"ok\":true}"), "ok")) return 116;

  std::cout << "POLL_JSON_PRIMITIVE_GRAMMAR_PASS valid=9/9 invalid=16/16\n";
  return 0;
}
"""


DEPTH_MAIN = r"""
String nestedComposite(unsigned depth, bool object) {
  std::string value;
  for (unsigned i = 0; i < depth; ++i) {
    if (object) value += "{\"k\":";
    else value += "[";
  }
  value += "0";
  for (unsigned i = 0; i < depth; ++i) {
    if (object) value += "}";
    else value += "]";
  }
  return String(value);
}

int main() {
  for (int object = 0; object < 2; ++object) {
    String accepted = nestedComposite(16, object != 0);
    int p = 0;
    if (!pollJsonSkipComposite(accepted, p) ||
        p != (int)accepted.length()) return object ? 131 : 121;

    String rejected = nestedComposite(17, object != 0);
    p = 0;
    if (pollJsonSkipComposite(rejected, p)) return object ? 132 : 122;
  }
  std::cout << "POLL_JSON_COMPOSITE_DEPTH_PASS max=16 rejected=17 arrays=1 objects=1\n";
  return 0;
}
"""

UTF8_MAIN = r"""
int main() {
  if (!pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xC2\xA2\"}"), "ok")) return 131;
  if (!pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xE2\x82\xAC\"}"), "ok")) return 132;
  if (!pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xF0\x9F\x92\xB0\"}"), "ok")) return 133;

  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xC0\xAF\"}"), "ok")) return 141;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\x80\"}"), "ok")) return 142;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xE2\x82\"}"), "ok")) return 143;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xED\xA0\x80\"}"), "ok")) return 144;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xF4\x90\x80\x80\"}"), "ok")) return 145;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xE2\x28\xA1\"}"), "ok")) return 146;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xF5\x80\x80\x80\"}"), "ok")) return 147;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xE0\x80\x80\"}"), "ok")) return 148;
  if (pollJsonTopLevelTrue(String("{\"ok\":true,\"meta\":\"\xF0\x80\x80\x80\"}"), "ok")) return 149;

  std::cout << "POLL_JSON_UTF8_VALIDATION_PASS valid=3/3 invalid=9/9\n";
  return 0;
}
"""
