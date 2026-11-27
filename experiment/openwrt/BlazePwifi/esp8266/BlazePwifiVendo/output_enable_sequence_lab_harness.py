"""C++ host harness for source-extracted startup GPIO sequencing."""
from pathlib import Path
import subprocess
import tempfile

CPP = r'''
#include <iostream>
#include <vector>

static constexpr int HIGH=1, LOW=0, INPUT_PULLUP=2, OUTPUT=3;
struct Event { int kind; int pin; int value; };
std::vector<Event> events;
void digitalWrite(int pin,int level){ events.push_back({1,pin,level}); }
void pinMode(int pin,int mode){ events.push_back({2,pin,mode}); }
static constexpr int FALLING=4, RISING=5;
int digitalPinToInterrupt(int pin){ return pin; }
void detachInterrupt(int) {}
void attachInterrupt(int,void (*)(void),int) {}
void coinEdgeISR() {}

int runCoinPin=4, runRelayPin=5, runLedPin=14;
bool runRelayActiveHigh=true, runLedActiveHigh=true, runCoinActiveLow=false;
@@WRITE_LOGICAL@@
@@CONFIGURE@@

int firstEvent(int kind,int pin,int value,int after=-1){
  for(size_t i=0;i<events.size();++i)
    if((int)i>after && events[i].kind==kind && events[i].pin==pin && events[i].value==value)
      return (int)i;
  return -1;
}

int scenario(bool relayActiveHigh,bool ledActiveHigh){
  events.clear();
  runCoinPin=4; runRelayPin=5; runLedPin=14;
  runRelayActiveHigh=relayActiveHigh; runLedActiveHigh=ledActiveHigh;
  configureRuntimePins(12,13,15);
  const int relayOffLevel=relayActiveHigh?LOW:HIGH;
  const int ledOffLevel=ledActiveHigh?LOW:HIGH;
  const int relayOff=firstEvent(1,13,relayOffLevel);
  const int relayOutput=firstEvent(2,13,OUTPUT);
  const int ledOff=firstEvent(1,15,ledOffLevel);
  const int ledOutput=firstEvent(2,15,OUTPUT);
  const int relayConfirm=firstEvent(1,13,relayOffLevel,relayOutput);
  const int ledConfirm=firstEvent(1,15,ledOffLevel,ledOutput);
  const int oldRelayOff=firstEvent(1,5,relayOffLevel);
  const int oldLedOff=firstEvent(1,14,ledOffLevel);
  if(relayOff<0 || relayOutput<0 || relayOff>=relayOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL relay OFF must precede OUTPUT mode\n"; return 10;
  }
  if(ledOff<0 || ledOutput<0 || ledOff>=ledOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL LED OFF must precede OUTPUT mode\n"; return 11;
  }
  if(relayConfirm<=relayOutput || ledConfirm<=ledOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL OFF level must be confirmed after OUTPUT mode\n"; return 12;
  }
  if(oldRelayOff<0 || oldLedOff<0 || oldRelayOff>=relayOutput || oldLedOff>=ledOutput){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL old outputs were not disabled before reassignment\n"; return 13;
  }
  const int relayActiveLevel=relayActiveHigh?HIGH:LOW;
  const int ledActiveLevel=ledActiveHigh?HIGH:LOW;
  if(firstEvent(1,13,relayActiveLevel)>=0){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL relay active level was written during startup\\n"; return 14;
  }
  if(firstEvent(1,15,ledActiveLevel)>=0){
    std::cerr<<"OUTPUT_SEQUENCE_FAIL LED active level was written during startup\\n"; return 15;
  }
  return 0;
}

int main(){
  const bool polarityPairs[][2]={{true,true},{true,false},{false,true},{false,false}};
  for(const auto &pair:polarityPairs){
    int result=scenario(pair[0],pair[1]);
    if(result) return result;
  }
  std::cout<<"OUTPUT_SEQUENCE_PASS all four independent relay/LED polarity combinations\n";
  return 0;
}
'''

def build_and_run(board: str, write_logical: str, configure: str, expect_pass: bool, mutation_label: str = "unsafe output order") -> None:
    code = CPP.replace("@@WRITE_LOGICAL@@", write_logical).replace("@@CONFIGURE@@", configure)
    with tempfile.TemporaryDirectory(prefix="phx-output-sequence-") as tmp:
        source_path = Path(tmp) / "sequence.cpp"
        binary_path = Path(tmp) / "sequence"
        source_path.write_text(code, encoding="utf-8")
        subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-O2",
             str(source_path), "-o", str(binary_path)],
            check=True,
        )
        result = subprocess.run([str(binary_path)], text=True, capture_output=True)
    if expect_pass and result.returncode != 0:
        raise SystemExit(
            f"{board}: production sequence failed ({result.returncode}): {result.stderr.strip()}"
        )
    if not expect_pass and result.returncode == 0:
        raise SystemExit(f"{board}: mutation survived: {mutation_label}")
    if expect_pass:
        print(f"{board}: {result.stdout.strip()}")
    else:
        print(f"{board}: mutation rejected: {mutation_label} at exit {result.returncode}")
