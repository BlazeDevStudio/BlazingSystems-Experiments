#!/usr/bin/env python3
"""Source-exact host regression for ESP8266 recovery from a rejected GPIO map.

The remote-config consumer remains intentionally dormant. This lab only proves
that its existing validated-pin recovery helper sequence is internally
consistent; it does not authenticate or activate remote configuration.
"""
from pathlib import Path
import subprocess
import tempfile

from firmware_lab_source import extract_function

SKETCH = Path(__file__).with_name("BlazePwifiVendo.ino")
FUNCTIONS = (
    "writeLogical",
    "validInputPullupPin",
    "validOutputPin",
    "runtimePinsSafe",
    "configureRuntimePins",
    "applyOutputs",
    "applyRemoteConfig",
)


def _program():
    source = SKETCH.read_text(encoding="utf-8")
    extracted = "\n\n".join(extract_function(source, name) for name in FUNCTIONS)
    stubs = r"""
#include <cstdint>
#include <iostream>
#include <string>

struct String : std::string {
  using std::string::string;
  using std::string::operator=;
  String()=default;
  String(const std::string &value):std::string(value){}
  size_t length() const { return size(); }
};

static constexpr int HIGH=1, LOW=0, INPUT=0, INPUT_PULLUP=2, OUTPUT=1;
static constexpr int FALLING=4, RISING=5;
static int pinModes[64], pinLevels[64];
static bool outputPolarityKnown=true, pinConfigSafe=false;
static bool runCoinActiveLow=true, runRelayActiveHigh=false, runLedActiveHigh=false;
static bool insertMode=false, controllerEnabled=true, coinEnabled=true;
static bool relayEnabled=true, ledEnabled=true, fsReady=true;
static bool journalRecoveryRequired=false, pendingReady=false;
static bool pollIntakeSuspended=false;
static uint8_t pendingPulses=0;
static uint32_t coinEdgeSequence=0, lastHandledCoinEdgeSequence=0;
static int runCoinPin=4, runRelayPin=5, runLedPin=14;
static int maxWifiRetries=6, wifiFailures=0, remoteRevision=0;
static uint16_t runDebounceMs=40, runPulseGroupMs=400;
static String activeTarget="", pendingTarget="", pendingNonce="";
static int forcedRelayPin=-1;

void pinMode(int pin,int mode){ pinModes[pin]=mode; }
void digitalWrite(int pin,int level){ pinLevels[pin]=level; }
int digitalPinToInterrupt(int pin){ return pin; }
void attachInterrupt(int,void(*)(),int){}
void detachInterrupt(int){}
void coinEdgeISR(){}
uint32_t snapshotCoinEdgeSequence(){ return coinEdgeSequence; }
bool quarantineCoinIngressTransition(){ return true; }
int jsonInt(const String&,const String &key,int fallback){
  return key=="relay_pin" && forcedRelayPin>=0 ? forcedRelayPin : fallback;
}
int boundedCoinDebounceMs(int value){
  return value<10?10:(value>1000?1000:value);
}
int constrain(int value,int low,int high){
  return value<low?low:(value>high?high:value);
}
struct FakeSerial {
  template<class T> void println(const T&){}
} Serial;
"""
    main = r"""
static void resetState(){
  for(int i=0;i<64;++i){ pinModes[i]=INPUT; pinLevels[i]=LOW; }
  outputPolarityKnown=true; pinConfigSafe=false;
  runCoinActiveLow=true; runRelayActiveHigh=false; runLedActiveHigh=false;
  insertMode=false; controllerEnabled=true; coinEnabled=true;
  relayEnabled=true; ledEnabled=true; fsReady=true;
  journalRecoveryRequired=false; pendingReady=false; pollIntakeSuspended=false;
  pendingPulses=0; coinEdgeSequence=0; lastHandledCoinEdgeSequence=0;
  runCoinPin=4; runRelayPin=5; runLedPin=14;
  maxWifiRetries=6; wifiFailures=0; remoteRevision=0;
  runDebounceMs=40; runPulseGroupMs=400;
  activeTarget=""; pendingTarget=""; pendingNonce="";
  forcedRelayPin=-1;
}

int main(){
  // A previously denied map recovers to a distinct, valid pin tuple.
  resetState();
  applyRemoteConfig(String("{\"config_revision\":1,\"coin_pin\":3,\"relay_pin\":12,\"led_pin\":13,\"coin_active_low\":1}"));
  if(!pinConfigSafe) return 1;
  if(runCoinPin!=3 || runRelayPin!=12 || runLedPin!=13) return 2;
  if(pinModes[runRelayPin]!=OUTPUT || pinModes[runLedPin]!=OUTPUT) return 3;
  if(pinLevels[runRelayPin]!=HIGH || pinLevels[runLedPin]!=HIGH) return 4;
  std::cout<<"ESP8266_REMOTE_CONFIG_VALID_PIN_RECOVERY_PASS\n";

  // A valid pin tuple cannot override unknown physical output polarity.
  resetState();
  outputPolarityKnown=false;
  applyRemoteConfig(String("{}"));
  if(pinConfigSafe || pinModes[runRelayPin]!=INPUT || pinModes[runLedPin]!=INPUT) return 4;
  std::cout<<"ESP8266_REMOTE_CONFIG_UNKNOWN_POLARITY_DENY_PASS\n";

  // An invalid/colliding relay pin must never reach OUTPUT mode.
  resetState();
  forcedRelayPin=99;
  applyRemoteConfig(String("{}"));
  if(pinConfigSafe || pinModes[runRelayPin]==OUTPUT || pinModes[runLedPin]==OUTPUT) return 5;
  std::cout<<"ESP8266_REMOTE_CONFIG_UNSAFE_PIN_DENY_PASS\n";
  return 0;
}
"""
    return stubs + "\n" + extracted + "\n" + main


def run_remote_config_pin_recovery_lab():
    program = _program()
    with tempfile.TemporaryDirectory(prefix="phx-esp8266-pin-recovery-") as folder:
        cpp = Path(folder) / "remote_config_pin_recovery.cpp"
        binary = Path(folder) / "remote_config_pin_recovery"
        cpp.write_text(program, encoding="utf-8")
        built = subprocess.run(
            ["g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
             "-Wno-unused-parameter", str(cpp), "-o", str(binary)],
            capture_output=True, text=True, timeout=30
        )
        if built.returncode:
            raise RuntimeError(
                "ESP8266 remote-config recovery lab compile failed:\n"
                + built.stderr[-3000:]
            )
        ran = subprocess.run(
            [str(binary)], capture_output=True, text=True, timeout=10
        )
        if ran.returncode:
            raise RuntimeError(
                "ESP8266 remote-config recovery lab failed with exit "
                + str(ran.returncode)
                + "\nstdout=" + ran.stdout + "\nstderr=" + ran.stderr
            )
        expected = (
            "ESP8266_REMOTE_CONFIG_VALID_PIN_RECOVERY_PASS",
            "ESP8266_REMOTE_CONFIG_UNKNOWN_POLARITY_DENY_PASS",
            "ESP8266_REMOTE_CONFIG_UNSAFE_PIN_DENY_PASS",
        )
        for marker in expected:
            if marker not in ran.stdout:
                raise RuntimeError(
                    "ESP8266 remote-config recovery lab missing marker: " + marker
                )
        print("ESP8266_REMOTE_CONFIG_PIN_RECOVERY_LAB_PASS 3/3")
        print(ran.stdout.strip())


if __name__ == "__main__":
    run_remote_config_pin_recovery_lab()
