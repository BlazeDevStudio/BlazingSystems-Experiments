#!/usr/bin/env python3
"""Execute actual extracted ESP quarantine functions against injected fake LittleFS.
No physical flash/relay/coin, money acceptance or reboot is claimed.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
boards = {
    "ESP32": root / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
    "ESP8266": root / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
}

template = r'''
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <string>
#include <iostream>

struct String : std::string {
  using std::string::string;
  using std::string::operator=;
  void replace(char from, char to) { for(char &c : *this) if(c==from) c=to; }
  void remove(size_t offset) { erase(offset); }
};
enum SeekMode { SeekSet };
struct FakeState {
  std::string bytes="OLD\n";
  bool failAppend=false, partialWrite=false, failRead=false, corruptRead=false;
} fs;
struct File {
  FakeState* state=nullptr;
  bool writable=false;
  size_t cursor=0;
  File()=default;
  File(FakeState* value, bool isWritable): state(value), writable(isWritable) {}
  explicit operator bool() const { return state != nullptr; }
  size_t size() const { return state ? state->bytes.size() : 0; }
  size_t write(const uint8_t* data,size_t len) {
    if(!state || !writable) return 0;
    if(state->partialWrite && len) len--;
    state->bytes.append((const char*)data,len);
    return len;
  }
  void flush() {}
  void close() { state=nullptr; }
  bool seek(size_t offset, SeekMode) {
    if(!state || writable || offset>state->bytes.size()) return false;
    cursor=offset;
    return true;
  }
  int read() {
    if(!state || writable || cursor>=state->bytes.size()) return -1;
    const auto value=(unsigned char)state->bytes[cursor++];
    return state->corruptRead ? (int)(value ^ 1) : value;
  }
};
struct FakeFS {
  File open(const char* path,const char* mode) {
    if(strcmp(path,"/quarantine.log")!=0) return {};
    if(strcmp(mode,"a")==0) return fs.failAppend ? File() : File(&fs,true);
    if(strcmp(mode,"r")==0) return fs.failRead ? File() : File(&fs,false);
    return {};
  }
} LittleFS;
struct FakeSerial { void println(const char*) {} } Serial;
unsigned long millis() { return 1234; }
bool fsReady=true;
uint8_t pendingPulses=4;
String pendingNonce="0011223344556677", pendingTarget="test-target";
int clearCalls=0;
void clearPending() { ++clearCalls; pendingPulses=0; pendingNonce.clear(); pendingTarget.clear(); }

@@EXTRACTED_FUNCTION@@

int main() {
  for(int test=0;test<8;test++) {
    fs=FakeState{};
    fsReady=true;
    pendingPulses=4;
    pendingNonce="0011223344556677";
    pendingTarget="test-target";
    clearCalls=0;
    if(test==0) fsReady=false;           // lost filesystem
    if(test==1) pendingPulses=0;         // no pending event
    if(test==2) fs.failAppend=true;      // cannot open log
    if(test==3) fs.partialWrite=true;    // short append
    if(test==4) fs.failRead=true;        // lost readback
    if(test==5) fs.corruptRead=true;     // bit-flipped readback
    if(test==6) pendingNonce=String(300,'N'); // oversized record
    bool shouldClear=(test==7);
    bool actual=quarantinePending(String("coin window expired"));
    if(actual!=shouldClear || clearCalls!=(shouldClear?1:0) ||
       (!shouldClear && pendingPulses!=(test==1?0:4))) {
      std::cerr<<"SOURCE_LAB_FAIL scenario "<<test<<"\n";
      return 1;
    }
    if(shouldClear && fs.bytes.find("NONCE=0011223344556677")==std::string::npos) {
      std::cerr<<"SOURCE_LAB_FAIL missing persisted nonce\n";
      return 2;
    }
  }
  std::cout<<"QUARANTINE_SOURCE_LAB_PASS 8/8 fault/positive cases\n";
  return 0;
}
'''

def extract_function(source):
    token = "bool quarantinePending(const String &reason){"
    start = source.find(token)
    if start < 0:
        raise ValueError("Expected quarantinePending function not present")
    depth = 0
    for offset in range(start + len(token) - 1, len(source)):
        if source[offset] == "{":
            depth += 1
        if source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[start:offset+1]
    raise ValueError("Unclosed quarantinePending body")

def run(board, path):
    body = extract_function(path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="phx-hw-") as workdir:
        source = Path(workdir) / "test.cpp"
        binary = Path(workdir) / "test"
        source.write_text(template.replace("@@EXTRACTED_FUNCTION@@", body), encoding="utf-8")
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                        "-O2", str(source), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    print(board, "exact source compiled and injected-host tests completed")

for board_name, file_path in boards.items():
    if not file_path.is_file():
        sys.exit("Missing actual firmware source: " + str(file_path))
    run(board_name, file_path)
print("HW-Q-LAB: 16/16 source-extracted synthetic host checks PASS; physical NOT TESTED")
