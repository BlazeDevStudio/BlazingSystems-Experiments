#!/usr/bin/env python3
"""Exact-source pending-journal write/readback and rotation fault-injection lab."""
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = (
    ("ESP32", ROOT / "esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT / "esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
)


def extract(source: str, signature: str) -> str:
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise AssertionError(f"unterminated {signature}")


CPP = r'''
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <map>
#include <string>
#include <vector>

struct String : std::string {
  using std::string::string;
  bool isEmpty() const { return empty(); }
};

static size_t testStrlcpy(char *dst,const char *src,size_t capacity) {
  size_t length=std::strlen(src);
  if(capacity) {
    size_t copy=std::min(length,capacity-1);
    std::memcpy(dst,src,copy);
    dst[copy]='\0';
  }
  return length;
}
#define strlcpy testStrlcpy

struct FakeDisk {
  std::map<std::string,std::vector<uint8_t>> files;
  bool mutateAfterClose=false;
  bool shortWrite=false;
  bool shortRead=false;
  bool readOpenFail=false;
  std::string removeFailPath;
  std::vector<unsigned> renameFailCalls;
  std::vector<unsigned> renameFalseNegativeCalls;
  unsigned renameCalls=0;
} disk;

struct File {
  std::string path;
  bool opened=false;
  bool writing=false;
  size_t cursor=0;

  explicit operator bool() const { return opened; }

  size_t size() const {
    if(!opened) return 0;
    auto found=disk.files.find(path);
    return found==disk.files.end()?0:found->second.size();
  }

  size_t write(const uint8_t *data,size_t length) {
    if(!opened || !writing) return 0;
    size_t count=(disk.shortWrite && length)?length-1:length;
    disk.files[path].assign(data,data+count);
    return count;
  }

  size_t readBytes(char *output,size_t length) {
    if(!opened || writing) return 0;
    const auto &bytes=disk.files[path];
    size_t count=std::min(length,bytes.size());
    if(disk.shortRead && count) --count;
    if(count) std::memcpy(output,bytes.data(),count);
    cursor+=count;
    return count;
  }

  void flush() {}

  void close() {
    if(opened && writing && disk.mutateAfterClose && !disk.files[path].empty())
      disk.files[path].back()^=0x01;
    opened=false;
  }
};

struct FakeLittleFS {
  bool exists(const char *path) const { return disk.files.count(path)!=0; }

  File open(const char *path,const char *mode) {
    if(std::strcmp(mode,"w")==0) {
      disk.files[path].clear();
      return File{path,true,true,0};
    }
    if(std::strcmp(mode,"r")==0) {
      if(disk.readOpenFail || !exists(path)) return {};
      return File{path,true,false,0};
    }
    return {};
  }

  bool remove(const char *path) {
    if(disk.removeFailPath==path) return false;
    return disk.files.erase(path)>0;
  }

  bool rename(const char *from,const char *to) {
    ++disk.renameCalls;
    if(std::find(disk.renameFailCalls.begin(),disk.renameFailCalls.end(),disk.renameCalls)!=disk.renameFailCalls.end())
      return false;
    const bool falseNegative=
      std::find(disk.renameFalseNegativeCalls.begin(),disk.renameFalseNegativeCalls.end(),disk.renameCalls)!=
      disk.renameFalseNegativeCalls.end();
    auto found=disk.files.find(from);
    if(found==disk.files.end() || disk.files.count(to)) return false;
    disk.files[to]=found->second;
    disk.files.erase(found);
    return !falseNegative;
  }
} LittleFS;

@@PENDING_STRUCT@@;
const uint32_t PENDING_MAGIC=@@MAGIC@@;
bool fsReady=true;
bool journalRecoveryRequired=false;
bool pendingPostAttempted=false;
uint8_t pendingPulses=3;
String pendingNonce="0011223344556677";
String pendingTarget="target001122334455667788";
@@CHECKSUM@@
@@READ@@
@@REMOVE_HELPER@@
@@SAVE@@

static void reset() {
  disk=FakeDisk{};
  fsReady=true;
  journalRecoveryRequired=false;
  pendingPostAttempted=false;
  pendingPulses=3;
  pendingNonce=String("0011223344556677");
  pendingTarget=String("target001122334455667788");
}

static std::vector<uint8_t> oldRecord() {
  PendingRecord record{};
  record.magic=PENDING_MAGIC;
  record.pulses=1;
  std::strcpy(record.nonce,"8899aabbccddeeff");
  std::strcpy(record.target,"oldtarget001122334455667788");
  record.checksum=pendingChecksum(record);
  const auto *start=reinterpret_cast<const uint8_t*>(&record);
  return std::vector<uint8_t>(start,start+sizeof(record));
}

int main() {
  reset();
  assert(savePending());
  assert(disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(!disk.files.count("/pending.bak"));
  assert(disk.renameCalls==1);
  PendingRecord stored{};
  std::memcpy(&stored,disk.files["/pending.dat"].data(),sizeof(stored));
  assert(stored.pulses==3 && stored.checksum==pendingChecksum(stored));

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.files["/pending.dat"].push_back(0xa5);
  const auto oversized=disk.files["/pending.dat"];
  PendingRecord oversizedRecord{};
  assert(!readPendingFile("/pending.dat",oversizedRecord));
  assert(disk.files["/pending.dat"]==oversized);
  assert(!journalRecoveryRequired);
  assert(disk.renameCalls==0);

  reset();
  PendingRecord dirtyNonce{};
  dirtyNonce.magic=PENDING_MAGIC;
  dirtyNonce.pulses=2;
  std::strcpy(dirtyNonce.nonce,"12345678");
  dirtyNonce.nonce[9]='x';
  std::strcpy(dirtyNonce.target,"target001");
  dirtyNonce.checksum=pendingChecksum(dirtyNonce);
  const auto *dirtyNonceStart=reinterpret_cast<const uint8_t*>(&dirtyNonce);
  disk.files["/pending.dat"]=
      std::vector<uint8_t>(dirtyNonceStart,dirtyNonceStart+sizeof(dirtyNonce));
  const auto dirtyNonceBytes=disk.files["/pending.dat"];
  PendingRecord dirtyNonceRead{};
  assert(!readPendingFile("/pending.dat",dirtyNonceRead));
  assert(disk.files["/pending.dat"]==dirtyNonceBytes);
  assert(!journalRecoveryRequired);
  assert(disk.renameCalls==0);

  reset();
  PendingRecord dirtyTarget{};
  dirtyTarget.magic=PENDING_MAGIC;
  dirtyTarget.pulses=2;
  std::strcpy(dirtyTarget.nonce,"12345678");
  std::strcpy(dirtyTarget.target,"target01");
  dirtyTarget.target[9]='x';
  dirtyTarget.checksum=pendingChecksum(dirtyTarget);
  const auto *dirtyTargetStart=reinterpret_cast<const uint8_t*>(&dirtyTarget);
  disk.files["/pending.dat"]=
      std::vector<uint8_t>(dirtyTargetStart,dirtyTargetStart+sizeof(dirtyTarget));
  const auto dirtyTargetBytes=disk.files["/pending.dat"];
  PendingRecord dirtyTargetRead{};
  assert(!readPendingFile("/pending.dat",dirtyTargetRead));
  assert(disk.files["/pending.dat"]==dirtyTargetBytes);
  assert(!journalRecoveryRequired);
  assert(disk.renameCalls==0);

  reset();
  pendingNonce=String("00112233445566778");
  assert(!savePending());
  assert(!journalRecoveryRequired);
  assert(disk.files.empty());
  assert(disk.renameCalls==0);

  reset();
  pendingTarget=String("ttttttttttttttttttttttttttttttttt");
  assert(pendingTarget.length()==33);
  assert(!savePending());
  assert(!journalRecoveryRequired);
  assert(disk.files.empty());
  assert(disk.renameCalls==0);

  reset();
  pendingNonce=String("1234567");
  assert(!savePending());
  assert(!journalRecoveryRequired);
  assert(disk.files.empty());
  assert(disk.renameCalls==0);

  reset();
  pendingTarget=String("1234567");
  assert(!savePending());
  assert(!journalRecoveryRequired);
  assert(disk.files.empty());
  assert(disk.renameCalls==0);

  reset();
  pendingPulses=21;
  assert(!savePending());
  assert(!journalRecoveryRequired);
  assert(disk.files.empty());
  assert(disk.renameCalls==0);

  reset();
  disk.mutateAfterClose=true;
  assert(!savePending());
  assert(!disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(disk.renameCalls==0);

  reset();
  disk.shortWrite=true;
  assert(!savePending());
  assert(!disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(disk.renameCalls==0);

  reset();
  disk.shortWrite=true;
  disk.removeFailPath="/pending.new";
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(!disk.files.count("/pending.dat"));
  assert(disk.files.count("/pending.new"));
  assert(disk.renameCalls==0);

  reset();
  disk.shortRead=true;
  assert(!savePending());
  assert(!disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(disk.renameCalls==0);

  reset();
  disk.shortRead=true;
  disk.removeFailPath="/pending.new";
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(!disk.files.count("/pending.dat"));
  assert(disk.files.count("/pending.new"));
  assert(disk.renameCalls==0);

  reset();
  disk.readOpenFail=true;
  assert(!savePending());
  assert(!disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(disk.renameCalls==0);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  assert(savePending());
  assert(disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(!disk.files.count("/pending.bak"));
  assert(disk.renameCalls==2);
  std::memcpy(&stored,disk.files["/pending.dat"].data(),sizeof(stored));
  assert(stored.pulses==3);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.files["/pending.bak"]=oldRecord();
  disk.removeFailPath="/pending.bak";
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(disk.files.count("/pending.dat"));
  assert(disk.files.count("/pending.new"));
  assert(disk.files.count("/pending.bak"));
  assert(disk.renameCalls==0);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.renameFailCalls={1};
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(disk.files.count("/pending.dat"));
  assert(disk.files.count("/pending.new"));
  assert(!disk.files.count("/pending.bak"));
  assert(disk.renameCalls==1);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.renameFailCalls={2};
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(!disk.files.count("/pending.dat"));
  assert(disk.files.count("/pending.new"));
  assert(disk.files.count("/pending.bak"));
  assert(disk.renameCalls==2);
  std::memcpy(&stored,disk.files["/pending.new"].data(),sizeof(stored));
  assert(stored.pulses==3);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.renameFalseNegativeCalls={1};
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(!disk.files.count("/pending.dat"));
  assert(disk.files.count("/pending.new"));
  assert(disk.files.count("/pending.bak"));
  assert(disk.renameCalls==1);
  std::memcpy(&stored,disk.files["/pending.new"].data(),sizeof(stored));
  assert(stored.pulses==3);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.renameFalseNegativeCalls={2};
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(disk.files.count("/pending.bak"));
  assert(disk.renameCalls==2);
  std::memcpy(&stored,disk.files["/pending.dat"].data(),sizeof(stored));
  assert(stored.pulses==3);

  reset();
  disk.files["/pending.dat"]=oldRecord();
  disk.removeFailPath="/pending.bak";
  assert(!savePending());
  assert(journalRecoveryRequired);
  assert(disk.files.count("/pending.dat"));
  assert(!disk.files.count("/pending.new"));
  assert(disk.files.count("/pending.bak"));
  assert(disk.renameCalls==2);
  std::memcpy(&stored,disk.files["/pending.dat"].data(),sizeof(stored));
  assert(stored.pulses==3);

  std::cout<<"PENDING_WRITE_READBACK_PASS 22/22 exact-source scenarios\n";
}
'''

for board, path in BOARDS:
    source = path.read_text(encoding="utf-8")
    magic = re.search(r"PENDING_MAGIC\s*=\s*(0x[0-9A-Fa-f]+)", source)
    assert magic, f"{board}: missing PENDING_MAGIC"
    save = extract(source, "bool savePending(){")
    assert 'readPendingFile("/pending.new",verify)' in save
    assert save.index('readPendingFile("/pending.new",verify)') < save.index('LittleFS.rename("/pending.new","/pending.dat")')
    cpp = CPP
    for marker, value in {
        "@@PENDING_STRUCT@@": extract(source, "struct PendingRecord {"),
        "@@MAGIC@@": magic.group(1),
        "@@CHECKSUM@@": extract(source, "uint32_t pendingChecksum("),
        "@@READ@@": extract(source, "bool readPendingFile("),
        "@@REMOVE_HELPER@@": extract(source, "bool removePendingCandidate("),
        "@@SAVE@@": save,
    }.items():
        cpp = cpp.replace(marker, value)

    with tempfile.TemporaryDirectory(prefix="phx-pending-write-") as tmp:
        cpp_path = Path(tmp) / "pending_write.cpp"
        binary = Path(tmp) / "pending_write"
        cpp_path.write_text(cpp, encoding="utf-8")
        subprocess.run(
            [
                "g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                "-fsanitize=address,undefined", str(cpp_path), "-o", str(binary),
            ],
            check=True,
        )
        subprocess.run([str(binary)], check=True)
    print(f"{board}: pending.new readback and rotation operations verified")

print("PHX-HARDWARE: pending write/readback and rotation PASS 22 cases x2 sketches")
