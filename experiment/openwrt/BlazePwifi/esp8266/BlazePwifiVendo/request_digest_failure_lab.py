#!/usr/bin/env python3
"""Source-exact failure injection for request SHA-256 digest dispatch.

The production SHA provider is replaced only at the hexDigest() boundary. Empty,
short, and non-hex outputs model crypto initialization/hash failures and malformed
provider output. The real signedBody() and post() functions are compiled from both
ESP sketches. A failed digest must not create an HTTP session or dispatch a request.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_lab_source import extract_function

ROOT = Path(__file__).resolve().parents[2]
BOARDS = {
    "ESP8266": ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "ESP32": ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
}



STUBS = r"""
#include <cstdint>
#include <iostream>
#include <string>

struct String : std::string {
  using std::string::string;
  String() = default;
  String(const char *value):std::string(value ? value : "") {}
  String(const std::string &value):std::string(value) {}
  size_t length() const { return size(); }
};
inline String operator+(const String &left,const String &right) {
  return String(static_cast<const std::string&>(left)+static_cast<const std::string&>(right));
}
inline String operator+(const String &left,const char *right) {
  return String(static_cast<const std::string&>(left)+std::string(right ? right : ""));
}
inline String operator+(const char *left,const String &right) {
  return String(std::string(left ? left : "")+static_cast<const std::string&>(right));
}

#ifdef TARGET_ESP32
struct Config {
  String key="test-key";
  String id="vendo-01";
  String server="127.0.0.1";
} cfg;
#else
struct Config {
  char key[32]="test-key";
  char id[32]="vendo-01";
  char server[64]="127.0.0.1";
} cfg;
#endif

String lastSentNonce;
String digestResult;
String postedBody;
int httpBeginCalls=0;
int httpPostCalls=0;

String freshNonce() { return String("nonce-123"); }
String esc(const String &value) { return value; }
String hexDigest(const String &) { return digestResult; }

constexpr int WL_CONNECTED=3;
struct Wifi { int status() const { return WL_CONNECTED; } } WiFi;
class WiFiClient {};
class HTTPClient {
 public:
  bool begin(WiFiClient &,const String &) { ++httpBeginCalls; return true; }
  void setTimeout(int) {}
  void addHeader(const char *,const char *) {}
  int POST(const String &body) { ++httpPostCalls; postedBody=body; return 200; }
  String getString() const { return String("ok"); }
  void end() {}
};
"""

MAIN = r"""
int main() {
  // Inject crypto initialization/hash failure and malformed provider output.
  digestResult=String("");
  if(signedBody(String("register"),String("0"),String("")).length()!=0) return 11;
  if(post(String("register")).length()!=0 || httpBeginCalls!=0 || httpPostCalls!=0) return 12;

  digestResult=String("abc");
  if(signedBody(String("poll"),String("0"),String("")).length()!=0) return 13;
  if(post(String("poll")).length()!=0 || httpBeginCalls!=0 || httpPostCalls!=0) return 14;

  digestResult=String(std::string(64,'G'));
  if(signedBody(String("register"),String("0"),String("")).length()!=0) return 15;
  if(post(String("register")).length()!=0 || httpBeginCalls!=0 || httpPostCalls!=0) return 16;

  // A valid 64-character hexadecimal digest must preserve the wire body.
  digestResult=String(std::string(64,'a'));
  const String body=signedBody(String("register"),String("0"),String(""));
  if(body.length()==0 || body.find("sig="+digestResult)==std::string::npos) return 17;
  const String response=post(String("register"));
  if(response!="ok" || httpBeginCalls!=1 || httpPostCalls!=1) return 18;
  if(postedBody.find("sig="+digestResult)==std::string::npos) return 19;

  std::cout << "REQUEST_DIGEST_FAILURE_DENY_PASS; empty/short/non-hex digests dispatch 0 HTTP requests; valid SHA-256 dispatches 1\n";
  return 0;
}
"""


def main() -> None:
    failed = []
    for board, path in BOARDS.items():
        source = path.read_text(encoding="utf-8")
        helper = extract_function(source, "validSha256Hex", required=False)
        signed = extract_function(source, "signedBody")
        post = extract_function(source, "post")
        code = ("#define TARGET_ESP32\n" if board == "ESP32" else "")
        code += STUBS + helper + "\n" + signed + "\n" + post + "\n" + MAIN
        with tempfile.TemporaryDirectory(prefix="phx-request-digest-") as folder:
            cpp = Path(folder) / "digest_test.cpp"
            binary = Path(folder) / "digest_test"
            cpp.write_text(code, encoding="utf-8")
            built = subprocess.run(
                ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                 "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
                capture_output=True, text=True, timeout=30,
            )
            if built.returncode:
                print(board, "COMPILE_FAIL", built.stderr[-4000:])
                failed.append(board)
                continue
            ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=10)
            print(board, "PASS" if ran.returncode == 0 else "FAIL",
                  ran.stdout.strip(), ran.stderr.strip())
            if ran.returncode:
                print(board, "EXPECTED_DENY_EXIT", ran.returncode)
                failed.append(board)
    if failed:
        raise SystemExit("request digest failure lab failed: " + ",".join(failed))


if __name__ == "__main__":
    main()
