#!/usr/bin/env python3
"""PHX-HARDWARE exact-source C++17 coin POST durability gate LAB.

Validates that failed flash saves or unreconciled boot journals cannot
dispatch pending RAM-only pulses to the network. Tests actual helper code,
not a Python reimplementation. NO real backend, money or hardware.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BOARDS = [
    ("ESP32", ROOT/"esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino"),
    ("ESP8266", ROOT/"esp8266/BlazePwifiVendo/BlazePwifiVendo.ino"),
]

def extract(source: str, signature: str) -> str:
    pos=source.find(signature)
    if pos<0:
        raise RuntimeError(f"Missing firmware signature {signature}")
    brace=source.find("{",pos)
    depth=0
    for end in range(brace,len(source)):
        if source[end]=="{":
            depth+=1
        elif source[end]=="}":
            depth-=1
            if depth==0:
                return source[pos:end+1]
    raise RuntimeError(f"Unterminated {signature}")

TEMPLATE=r'''
#include <cstdint>
#include <iostream>
bool fsReady=false, journalRecoveryRequired=false, pendingReady=false, pendingPostAttempted=false;
uint8_t pendingPulses=0;
@@FUNCTION@@
struct Case{
  bool fs, recovery, ready;
  uint8_t pulses;
  bool expected;
};
int main(){
  const Case cases[]={
    {true,false,true,3,true},
    {true,false,true,1,true},
    {true,false,true,20,true},
    {true,false,false,3,false},
    {false,false,true,3,false},
    {true,true,true,3,false},
    {true,false,true,0,false},
    {false,true,true,3,false},
    {false,false,false,0,false},
  };
  for(unsigned i=0;i<sizeof(cases)/sizeof(cases[0]);++i){
    fsReady=cases[i].fs;
    journalRecoveryRequired=cases[i].recovery;
    pendingReady=cases[i].ready;
    pendingPulses=cases[i].pulses;
    const bool actual=canAttemptCoinPost();
    if(actual!=cases[i].expected){
      std::cerr<<"COIN_POST_GATE_FAIL case "<<i<<": got "<<actual<<"\n";
      return 1;
    }
  }
  pendingPostAttempted=true;
  fsReady=true; journalRecoveryRequired=false; pendingReady=true; pendingPulses=3;
  if(canAttemptCoinPost()){
    std::cerr<<"COIN_POST_GATE_FAIL attempt marker must block dispatch\\n";
    return 2;
  }
  std::cout<<"COIN_POST_GATE_PASS 10/10 exact helper scenarios, not hardware evidence\n";
  return 0;
}
'''
for board,path in BOARDS:
    source=path.read_text(encoding="utf-8")
    func=extract(source,"bool canAttemptCoinPost(){")
    if "fsReady" not in func or "!journalRecoveryRequired" not in func or "pendingReady" not in func or "pendingPulses>0" not in func:
        raise SystemExit(f"{board}: missing required pending dispatch condition")
    loop=extract(source,"void loop(){")
    if "if(canAttemptCoinPost() && WiFi.status()==WL_CONNECTED" not in loop:
        raise SystemExit(f"{board}: coin post bypasses journal guard")
    if 'post("coin"' not in loop:
        raise SystemExit(f"{board}: unexpected coin post call site")
    if "if(!savePending())" not in loop or "fsReady=false;" not in loop:
        raise SystemExit(f"{board}: failed journal write handling missing")
    code=TEMPLATE.replace("@@FUNCTION@@",func)
    with tempfile.TemporaryDirectory(prefix="phx-post-gate-") as tmp:
        sourcepath=Path(tmp)/"gate.cpp"
        outputpath=Path(tmp)/"gate"
        sourcepath.write_text(code,encoding="utf-8")
        subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror","-O2",
                        str(sourcepath),"-o",str(outputpath)],check=True)
        subprocess.run([str(outputpath)],check=True)
    print(f"{board}: actual canAttemptCoinPost() compiled and tested")
print("PHX-HARDWARE: 20/20 source-extracted coin POST gate cases PASS; actual money NOT TESTED")
