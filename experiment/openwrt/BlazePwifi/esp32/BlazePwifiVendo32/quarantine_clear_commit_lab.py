#!/usr/bin/env python3
"""PHX-HARDWARE: source-extracted quarantine clear/commit failure tests.

Compiles the actual clearPending() and quarantinePending() helpers from both
ESP sketches. readPendingFile() and appendQuarantineRecord() are controlled
boundaries here; their parsers and append/readback behavior are tested by the
existing source-extracted labs. This lab tests exact pending identity, deletion
verification, and failure propagation. SIMULATED only.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)

CPP = r'''
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <string>

struct String : std::string {
  using std::string::string;
  size_t length() const { return size(); }
};
struct PendingRecord {
  uint32_t magic=0;
  uint8_t pulses=0;
  char nonce[17]{};
  char target[33]{};
  uint32_t checksum=0;
};
static bool fsReady=true;
static uint8_t pendingPulses=4;
static bool pendingReady=true;
static String pendingNonce="nonce00112233445";
static String pendingTarget="target0011223344";
static uint32_t lastSend=77;
static int readCalls=0, removeCalls=0, appendCalls=0;
static bool readFail=false, appendAllowed=true;
static std::string failRemovePath, noDeletePath;
static std::map<std::string,PendingRecord> pendingFiles;

struct FakeLittleFS {
  bool exists(const char *path) const {
    return pendingFiles.find(path)!=pendingFiles.end();
  }
  bool remove(const char *path) {
    ++removeCalls;
    const std::string key(path);
    if(key==failRemovePath) return false;
    if(key==noDeletePath) return true;
    return pendingFiles.erase(key)==1;
  }
} LittleFS;

bool readPendingFile(const char *path,PendingRecord &out) {
  ++readCalls;
  if(readFail) return false;
  const auto it=pendingFiles.find(path);
  if(it==pendingFiles.end()) return false;
  out=it->second;
  return true;
}
bool appendQuarantineRecord(const String &) {
  ++appendCalls;
  return appendAllowed;
}
struct FakeSerial {
  template<class T> void println(const T &) {}
} Serial;

@@CLEAR@@
@@QUARANTINE@@

static PendingRecord makeRecord(uint8_t pulses=4,
                                const char *nonce="nonce00112233445",
                                const char *target="target0011223344") {
  PendingRecord r{};
  r.magic=0x42504332U;
  r.pulses=pulses;
  std::strncpy(r.nonce,nonce,sizeof(r.nonce)-1);
  std::strncpy(r.target,target,sizeof(r.target)-1);
  return r;
}
static void reset() {
  pendingFiles.clear();
  failRemovePath.clear();
  noDeletePath.clear();
  fsReady=true;
  pendingPulses=4;
  pendingReady=true;
  pendingNonce="nonce00112233445";
  pendingTarget="target0011223344";
  lastSend=77;
  readCalls=removeCalls=appendCalls=0;
  readFail=false;
  appendAllowed=true;
}
int main() {
  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  appendAllowed=false;
  if(quarantinePending("window expired") || appendCalls!=1 ||
     readCalls!=0 || removeCalls!=0 ||
     !LittleFS.exists("/pending.dat") || pendingPulses!=4 ||
     !pendingReady || !fsReady) {
    std::cerr<<"APPEND_FAILURE mutated pending state\n"; return 1;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  if(!quarantinePending("window expired") || appendCalls!=1 ||
     readCalls!=1 || removeCalls!=1 ||
     LittleFS.exists("/pending.dat") || pendingPulses!=0 ||
     pendingReady || !pendingNonce.empty() || !pendingTarget.empty() ||
     lastSend!=0 || !fsReady) {
    std::cerr<<"SUCCESS did not clear exactly one verified pending record\n"; return 2;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  failRemovePath="/pending.dat";
  if(quarantinePending("window expired") || appendCalls!=1 ||
     readCalls!=1 || removeCalls!=1 ||
     !LittleFS.exists("/pending.dat") || pendingPulses!=4 ||
     !pendingReady || pendingNonce!="nonce00112233445" ||
     pendingTarget!="target0011223344" || fsReady) {
    std::cerr<<"REMOVE_FAILURE did not preserve pending event and deny\n"; return 3;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  noDeletePath="/pending.dat";
  if(quarantinePending("window expired") ||
     !LittleFS.exists("/pending.dat") || pendingPulses!=4 ||
     !pendingReady || fsReady) {
    std::cerr<<"REMOVE_LIES_ABOUT_SUCCESS was not rejected\n"; return 4;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  pendingFiles["/pending.bak"]=makeRecord();
  if(quarantinePending("window expired") || readCalls!=0 ||
     removeCalls!=0 || pendingFiles.size()!=2 ||
     pendingPulses!=4 || !pendingReady || fsReady) {
    std::cerr<<"MULTIPLE_CANDIDATES were not preserved\n"; return 5;
  }

  reset();
  if(quarantinePending("window expired") || readCalls!=0 ||
     removeCalls!=0 || !pendingFiles.empty() ||
     pendingPulses!=4 || !pendingReady || fsReady) {
    std::cerr<<"MISSING_CANDIDATE did not deny\n"; return 6;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord(4,"wrongnonce12345","target0011223344");
  if(quarantinePending("window expired") || readCalls!=1 ||
     removeCalls!=0 || pendingFiles.size()!=1 ||
     pendingPulses!=4 || !pendingReady || fsReady) {
    std::cerr<<"MISMATCHED_RECORD was not preserved\n"; return 7;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  readFail=true;
  if(quarantinePending("window expired") || readCalls!=1 ||
     removeCalls!=0 || !LittleFS.exists("/pending.dat") ||
     pendingPulses!=4 || !pendingReady || fsReady) {
    std::cerr<<"READ_FAILURE did not deny\n"; return 8;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  fsReady=false;
  if(quarantinePending("window expired") || readCalls!=0 ||
     removeCalls!=0 || !LittleFS.exists("/pending.dat") ||
     pendingPulses!=4 || !pendingReady || fsReady) {
    std::cerr<<"FILESYSTEM_UNAVAILABLE did not deny\n"; return 9;
  }

  reset();
  pendingFiles["/pending.dat"]=makeRecord();
  pendingPulses=0;
  if(quarantinePending("window expired") ||
     !LittleFS.exists("/pending.dat") || pendingReady==false ||
     fsReady) {
    std::cerr<<"EMPTY_EVENT did not deny\n"; return 10;
  }

  std::cout<<"QUARANTINE_CLEAR_COMMIT_PASS 10/10 scenarios\n";
  return 0;
}
'''

def extract_function(source: str, signature: str) -> str:
    pos = source.find(signature)
    if pos < 0:
        raise RuntimeError("missing production function: " + signature)
    brace = source.find("{", pos)
    if brace < 0:
        raise RuntimeError("missing function body: " + signature)
    depth = 0
    quote = None
    escaped = False
    for i in range(brace, len(source)):
        ch = source[i]
        if quote is not None:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return source[pos:i + 1]
    raise RuntimeError("unterminated production function: " + signature)

def compile_and_run(board: str, cpp: str, directory: Path, suffix: str):
    source_path = directory / f"{board.lower()}_{suffix}.cpp"
    binary_path = directory / f"{board.lower()}_{suffix}"
    source_path.write_text(cpp, encoding="utf-8")
    built = subprocess.run(
        ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
         str(source_path), "-o", str(binary_path)],
        capture_output=True, text=True, timeout=30
    )
    if built.returncode:
        raise RuntimeError(f"{board} {suffix} compile failed:\n{built.stderr[-3000:]}")
    return subprocess.run([str(binary_path)], capture_output=True, text=True, timeout=10)

def main():
    with tempfile.TemporaryDirectory(prefix="phx-quarantine-clear-") as temp_name:
        directory = Path(temp_name)
        for board, path in BOARDS:
            source = path.read_text(encoding="utf-8")
            clear = extract_function(source, "bool clearPending()")
            quarantine = extract_function(source, "bool quarantinePending(")
            if "return clearPending();" not in quarantine:
                raise RuntimeError(
                    f"{board}: quarantinePending must propagate clearPending failure"
                )
            cpp = CPP.replace("@@CLEAR@@", clear).replace("@@QUARANTINE@@", quarantine)
            result = compile_and_run(board, cpp, directory, "clear")
            if result.returncode:
                print(result.stdout, end="")
                print(result.stderr, end="")
                raise RuntimeError(f"{board}: clear/commit scenarios failed ({result.returncode})")
            print(f"{board}: {result.stdout.strip()}")

            mutated_quarantine = quarantine.replace(
                "return clearPending();", "clearPending(); return true;", 1
            )
            if mutated_quarantine == quarantine:
                raise RuntimeError(f"{board}: ignored-clear-result mutation anchor missing")
            mutant_cpp = CPP.replace("@@CLEAR@@", clear).replace(
                "@@QUARANTINE@@", mutated_quarantine
            )
            mutant = compile_and_run(board, mutant_cpp, directory, "mutant")
            if mutant.returncode != 3 or "REMOVE_FAILURE" not in mutant.stderr:
                print(mutant.stdout, end="")
                print(mutant.stderr, end="")
                raise RuntimeError(
                    f"{board}: ignored clearPending result mutation escaped (exit={mutant.returncode})"
                )
            print(f"{board}: MUTATION_REJECTED ignored clearPending result (exit=3)")

    print("PHX-HARDWARE: 10/10 clear/commit scenarios per board; SIMULATED ONLY")

if __name__ == "__main__":
    main()
