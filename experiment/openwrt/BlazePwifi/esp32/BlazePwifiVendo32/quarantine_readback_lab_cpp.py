"""C++17 source-extracted quarantine harness template.

Keep this file data-only. The companion runner owns source extraction,
board parity, temporary compilation and scenario execution.
"""

CPP = r'''
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <string>
struct String : std::string {
  using std::string::string;
  void remove(size_t index){erase(index);}
};
static constexpr size_t QUARANTINE_MAX_BYTES=4096;
static bool fsReady=true;
static bool journalRecoveryRequired=false;
// Mirrors the production one-shot gate state used by canAttemptCoinPost().
static bool pendingPostAttempted=false;
bool outputPolarityKnown=true, pinConfigSafe=true;
static bool attemptMarkerExists=true, attemptMarkerValid=true;
static uint8_t pendingPulses=4;
static bool pendingReady=true;
static String pendingNonce="nonce00112233445";
static String pendingTarget="target0011223344";
struct PendingRecord { uint8_t pulses=0; char nonce[17]{}; char target[33]{}; };
static PendingRecord attemptMarker{};
bool readPendingFile(const char *path,PendingRecord &out){
  if(std::strcmp(path,"/pending.attempt")!=0 || !attemptMarkerExists || !attemptMarkerValid) return false;
  out=attemptMarker;
  return true;
}
@@SOURCE_ATTEMPT_MATCH@@
static int clearCount=0;
static bool clearAllowed=true;
unsigned long millis(){return 1234UL;}
bool clearPending(){
  ++clearCount;
  if(!clearAllowed){journalRecoveryRequired=true; return false;}
  pendingPulses=0; pendingNonce.clear(); pendingTarget.clear();
  // Production clearPending resets this only after durable disposition succeeds.
  pendingPostAttempted=false;
  attemptMarkerExists=false;
  return true;
}
struct FakeSerial {
  template<class T> void println(const T&) {}
} Serial;
enum SeekMode { SeekSet };
struct FakeDisk {
  std::string bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
  bool priorOpenFail=false, appendOpenFail=false, verifyOpenFail=false;
  bool logExists=true;
  bool shortWrite=false, mutateAfterClose=false, mutatePrefixAfterClose=false, mutateOnRead=false;
  bool removeOneByteAfterClose=false;
  bool hasWritten=false;
} disk;
struct File {
  FakeDisk* d=nullptr;
  bool writing=false;
  size_t cursor=0;
  File()=default;
  File(FakeDisk* p,bool writable):d(p),writing(writable){}
  explicit operator bool() const {return d!=nullptr;}
  size_t size() const{return d?d->bytes.size():0;}
  size_t write(const uint8_t* buf,size_t len){
    if(!d || !writing)return 0;
    size_t n=(d->shortWrite && len)?len-1:len;
    d->bytes.append((const char*)buf,n);
    d->hasWritten=true;
    return n;
  }
  void flush(){}
  void close(){
    if(d && writing){
      if(d->mutateAfterClose && !d->bytes.empty()) d->bytes.back()='Z';
      // Simulate same-size corruption of an older record while the new suffix stays intact.
      if(d->mutatePrefixAfterClose && !d->bytes.empty()) d->bytes[0]='U';
      if(d->removeOneByteAfterClose && !d->bytes.empty()) d->bytes.pop_back();
    }
    d=nullptr;
  }
  bool seek(size_t offset,SeekMode){
    if(!d || writing || offset>d->bytes.size())return false;
    cursor=offset;
    return true;
  }
  size_t available() const{return d && !writing && cursor<d->bytes.size()?d->bytes.size()-cursor:0;}
  int read(){
    if(!d || writing || cursor>=d->bytes.size())return -1;
    int byte=(unsigned char)d->bytes[cursor++];
    return (d->mutateOnRead && d->hasWritten)?(byte^1):byte;
  }
};
struct FakeLittleFS {
  bool exists(const char* path){
    return strcmp(path,"/quarantine.log")==0 && disk.logExists;
  }
  File open(const char* path,const char* mode){
    if(strcmp(path,"/quarantine.log")!=0)return {};
    if(strcmp(mode,"a")==0){
      if(disk.appendOpenFail)return {};
      // Append mode creates the first quarantine log when it is absent.
      disk.logExists=true;
      return File(&disk,true);
    }
    if(strcmp(mode,"r")==0){
      if(!disk.logExists || (!disk.hasWritten && disk.priorOpenFail) ||
         (disk.hasWritten && disk.verifyOpenFail)) return {};
      return File(&disk,false);
    }
    return {};
  }
} LittleFS;

@@SOURCE_COIN_POST_GATE@@
@@SOURCE_FIELD_ESCAPE@@
@@SOURCE_ENCODE@@
@@SOURCE_TOKEN_VALID@@
@@SOURCE_RECORD_VALID@@
@@SOURCE_CRC32_UPDATE@@
@@SOURCE_INSPECT@@
@@SOURCE_APPEND@@
@@SOURCE_QUARANTINE@@
String legacyQuarantineLogField(const String &value,size_t maxLen){
  String out;
  out.reserve(maxLen);
  size_t i=0;
  for(;i<value.length();++i){
    const unsigned char c=(unsigned char)value[i];
    const char *escaped=nullptr;
    if(c=='\\') escaped="\\\\";
    else if(c=='\r') escaped="\\r";
    else if(c=='\n') escaped="\\n";
    else if(c=='\t') escaped="\\t";
    else if(c==' ' && i+8<=value.length() &&
            ((value[i+1]=='R' && value[i+2]=='E' && value[i+3]=='A' &&
              value[i+4]=='S' && value[i+5]=='O' && value[i+6]=='N' && value[i+7]=='=') ||
             (value[i+1]=='T' && value[i+2]=='A' && value[i+3]=='R' &&
              value[i+4]=='G' && value[i+5]=='E' && value[i+6]=='T' && value[i+7]=='=')))
      escaped="\\x20";
    if(escaped){
      const size_t escapedLength=strlen(escaped);
      if(out.length()+escapedLength>maxLen) break;
      out+=escaped;
    } else {
      if(out.length()+1>maxLen) break;
      out+=(c<0x20 || c==0x7f)?'?':(char)c;
    }
  }
  if(i<value.length() && maxLen>=3){
    while(out.length()+3>maxLen) out.remove(out.length()-1);
    out+="...";
  }
  return out;
}
int main(){
  String boundaryValue(124,'A');
  boundaryValue += " REASON=tail";
  const String boundaryEncoded=quarantineLogField(boundaryValue,128);
  if(boundaryEncoded.length()!=127 ||
     boundaryEncoded.substr(0,124)!=String(124,'A') ||
     boundaryEncoded.substr(124)!="..."){
    std::cerr<<"QUARANTINE_FIELD_ESCAPE_BOUNDARY_FAIL board=BOARD_NAME actual="
             <<boundaryEncoded<<std::endl;
    return 62;
  }
  std::cout<<"QUARANTINE_FIELD_ESCAPE_BOUNDARY_PASS board=BOARD_NAME"<<std::endl;

  String targetBoundaryValue(124,'B');
  targetBoundaryValue += " TARGET=tail";
  const String targetBoundaryEncoded=quarantineLogField(targetBoundaryValue,128);
  if(targetBoundaryEncoded.length()!=127 ||
     targetBoundaryEncoded.substr(0,124)!=String(124,'B') ||
     targetBoundaryEncoded.substr(124)!="..."){
    std::cerr<<"QUARANTINE_TARGET_ESCAPE_BOUNDARY_FAIL board=BOARD_NAME actual="
             <<targetBoundaryEncoded<<std::endl;
    return 63;
  }
  std::cout<<"QUARANTINE_TARGET_ESCAPE_BOUNDARY_PASS board=BOARD_NAME"<<std::endl;

  String exactBoundaryValue(117,'C');
  exactBoundaryValue += " REASON=";
  const String exactBoundaryEncoded=quarantineLogField(exactBoundaryValue,128);
  if(exactBoundaryEncoded.length()!=128 ||
     exactBoundaryEncoded.substr(121)!="REASON="){
    std::cerr<<"QUARANTINE_FIELD_EXACT_LIMIT_FAIL board=BOARD_NAME actual="
             <<exactBoundaryEncoded<<std::endl;
    return 64;
  }
  std::cout<<"QUARANTINE_FIELD_EXACT_LIMIT_PASS board=BOARD_NAME"<<std::endl;
  const char escapeAtoms[]={'\\','\r','\n','\t'};
  for(size_t atomIndex=0;atomIndex<sizeof(escapeAtoms)/sizeof(escapeAtoms[0]);++atomIndex){
    String atomBoundaryValue(124,'D');
    atomBoundaryValue += escapeAtoms[atomIndex];
    atomBoundaryValue += "XYZ";
    const String atomBoundaryEncoded=quarantineLogField(atomBoundaryValue,128);
    if(atomBoundaryEncoded.length()!=127 ||
       atomBoundaryEncoded.substr(0,124)!=String(124,'D') ||
       atomBoundaryEncoded.substr(124)!="..."){
      std::cerr<<"QUARANTINE_ESCAPE_ATOM_BOUNDARY_FAIL board=BOARD_NAME atom="
               <<atomIndex<<" actual="<<atomBoundaryEncoded<<std::endl;
      return 65;
    }
  }
  std::cout<<"QUARANTINE_ESCAPE_ATOM_BOUNDARY_PASS 4/4 board=BOARD_NAME"<<std::endl;

  auto escapesComplete=[](const String &encoded){
    for(size_t i=0;i<encoded.length();++i){
      if(encoded[i]!='\\') continue;
      if(i+1>=encoded.length()) return false;
      if(encoded[i+1]=='\\' || encoded[i+1]=='r' ||
         encoded[i+1]=='n' || encoded[i+1]=='t'){
        ++i;
        continue;
      }
      if(i+3<encoded.length() && encoded.substr(i,4)=="\\x20"){
        i+=3;
        continue;
      }
      return false;
    }
    return true;
  };
  String sweepValue(118,'F');
  sweepValue += "\\\r\n\t REASON=tail TARGET=tail";
  for(size_t limit=0;limit<=160;++limit){
    const String swept=quarantineLogField(sweepValue,limit);
    if(swept.length()>limit || !escapesComplete(swept)){
      std::cerr<<"QUARANTINE_ESCAPE_LIMIT_SWEEP_FAIL board=BOARD_NAME limit="
               <<limit<<" actual="<<swept<<std::endl;
      return 66;
    }
  }
  std::cout<<"QUARANTINE_ESCAPE_LIMIT_SWEEP_PASS 161/161 board=BOARD_NAME"<<std::endl;
  for(size_t atomIndex=0;atomIndex<sizeof(escapeAtoms)/sizeof(escapeAtoms[0]);++atomIndex){
    String legacyValue(124,'D');
    legacyValue += escapeAtoms[atomIndex];
    legacyValue += "XYZ";
    const String legacyEncoded=legacyQuarantineLogField(legacyValue,128);
    if(escapesComplete(legacyEncoded) || legacyEncoded.substr(124)!="\\..."){
      std::cerr<<"QUARANTINE_LEGACY_ESCAPE_MUTATION_NOT_REPRODUCED board=BOARD_NAME atom="
               <<atomIndex<<" actual="<<legacyEncoded<<std::endl;
      return 67;
    }
  }
  String legacyDelimiterValue(124,'A');
  legacyDelimiterValue += " REASON=tail";
  const String legacyDelimiterEncoded=legacyQuarantineLogField(legacyDelimiterValue,128);
  if(escapesComplete(legacyDelimiterEncoded) ||
     legacyDelimiterEncoded.substr(124)!="\\..."){
    std::cerr<<"QUARANTINE_LEGACY_DELIMITER_MUTATION_NOT_REPRODUCED board=BOARD_NAME actual="
             <<legacyDelimiterEncoded<<std::endl;
    return 68;
  }
  std::cout<<"QUARANTINE_LEGACY_DANGLING_ESCAPE_REPRODUCED 5/5 board=BOARD_NAME"<<std::endl;
  for(int scenario=0;scenario<36;scenario++){
    disk=FakeDisk{};
    clearCount=0;
    clearAllowed=true;
    fsReady=true;
    journalRecoveryRequired=false;
    pendingPostAttempted=true;
    pendingPulses=4;
    pendingReady=true;
    pendingNonce="nonce00112233445";
    pendingTarget="target0011223344";
    attemptMarker=PendingRecord{};
    attemptMarker.pulses=pendingPulses;
    std::strcpy(attemptMarker.nonce,pendingNonce.c_str());
    std::strcpy(attemptMarker.target,pendingTarget.c_str());
    attemptMarkerExists=true;
    attemptMarkerValid=true;
    if(scenario==1) fsReady=false;
    if(scenario==2) pendingPulses=0;
    if(scenario==3) disk.priorOpenFail=true;
    if(scenario==4) disk.appendOpenFail=true;
    if(scenario==5) disk.shortWrite=true;
    if(scenario==6) disk.verifyOpenFail=true;
    if(scenario==7) disk.removeOneByteAfterClose=true;
    if(scenario==8) disk.mutateAfterClose=true; // corrupts final newline
    if(scenario==9) disk.mutateOnRead=true; // verification read fault only
    if(scenario==10){
      const std::string valid="TIME=1 PULSES=1 NONCE=old TARGET=old REASON=old\n";
      disk.bytes.clear();
      while(disk.bytes.size()<=QUARANTINE_MAX_BYTES) disk.bytes+=valid;
    }
    if(scenario==11) clearAllowed=false;
    String reason="window expired";
    if(scenario==12) reason=String("bad\nRECORD=forged\t\\");
    if(scenario==13) journalRecoveryRequired=true;
    if(scenario==14)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=earlier\n";
    if(scenario==15)
      disk.bytes+="TIME=9 PULSES=4 NONCE=nonce00112233445";
    if(scenario==16)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=earlier\n"
                 "TIME=9 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=duplicate\n";
    if(scenario==17)
      disk.bytes="TIME=not-a-number PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=forged-but-complete\n";
    if(scenario==18)
      disk.bytes="TIME=4294967296 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=overflowed-time\n";
    if(scenario==19) pendingPostAttempted=false; // attempted state missing
    if(scenario==20) attemptMarkerExists=false;
    if(scenario==21) attemptMarkerValid=false;
    if(scenario==22) std::strcpy(attemptMarker.nonce,"wrongnonce123456");
    // Malformed prior quarantine records must never authorize pending deletion.
    if(scenario==23)
      disk.bytes="TIME=1 PULSES=not-a-number NONCE=oldnonce TARGET=oldtarget REASON=old\n";
    if(scenario==24)
      disk.bytes="TIME=1 PULSES=21 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
    if(scenario==25)
      disk.bytes="TIME=1 PULSES=1 NONCE= TARGET=oldtarget REASON=old\n";
    if(scenario==26)
      disk.bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET= REASON=old\n";
    if(scenario==27)
      disk.bytes="TIME=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=\n";
    if(scenario==28)
      disk.bytes="TIME=1 PULSES=1 PULSES=1 NONCE=oldnonce TARGET=oldtarget REASON=old\n";
    if(scenario==29){
      pendingTarget="target0011223344 REASON=earlier";
      std::strcpy(attemptMarker.target,pendingTarget.c_str());
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=earlier REASON=window expired\n";
    }
    if(scenario==30){
      pendingTarget="target with spaces";
      std::strcpy(attemptMarker.target,pendingTarget.c_str());
    }
    if(scenario==31) reason=String("window REASON=expired");
    if(scenario==32)
      disk.bytes="TIME=8 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window REASON=expired\n";
    // First-ever quarantine record: no file exists before append.
    if(scenario==33){ disk.logExists=false; disk.bytes.clear(); }
    // First-ever append open failure must not create a log or clear pending.
    if(scenario==34){ disk.logExists=false; disk.bytes.clear(); disk.appendOpenFail=true; }
    // Scenario 35 corrupts a pre-existing record but leaves the appended suffix exact.
    if(scenario==35) disk.mutatePrefixAfterClose=true;
    const std::string bytesBefore=disk.bytes;
    bool expectClear=(scenario==0 || scenario==12 || scenario==14 || scenario==31 || scenario==33);
    bool expectClearAttempt=expectClear || scenario==11;
    bool expectRecovery=scenario==1 || scenario==3 || scenario==4 ||
                        (scenario>=5 && scenario<=10) ||
                        scenario==2 || scenario==11 || scenario==13 || scenario==15 || scenario==16 || scenario==17 || scenario==18 || scenario==34 || (scenario>=19 && scenario!=31 && scenario!=33);
    bool ok=quarantinePending(reason);
    if(ok!=expectClear || clearCount!=(expectClearAttempt?1:0) ||
       (!expectClear && pendingPulses!=(scenario==2?0:4)) ||
       (scenario==12 &&
        (std::count(disk.bytes.begin(),disk.bytes.end(),'\n')!=2 ||
         disk.bytes.find("bad\\nRECORD=forged\\t\\\\")==std::string::npos)) ||
       (scenario==4 && disk.bytes!=bytesBefore) ||
       (scenario==10 && disk.bytes!=bytesBefore) ||
       (scenario==14 && disk.bytes!=bytesBefore) ||
       (scenario==15 && disk.bytes!=bytesBefore) ||
       (scenario==16 && disk.bytes!=bytesBefore) ||
       (scenario==17 && disk.bytes!=bytesBefore) ||
       (scenario==18 && disk.bytes!=bytesBefore) ||
       (scenario>=19 && scenario!=31 && scenario!=33 && scenario!=35 && disk.bytes!=bytesBefore) ||
       (scenario==31 && (disk.bytes.find(std::string("window")+char(92)+"x20REASON=expired")==std::string::npos || disk.bytes.find("window REASON=expired")!=std::string::npos)) ||
       (scenario==33 && (!disk.logExists || disk.bytes.empty() ||
         disk.bytes.find("TIME=1234 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window expired") == std::string::npos)) ||
       (scenario==34 && (disk.logExists || !disk.bytes.empty())) ||
       (scenario==35 && (disk.bytes.empty() || disk.bytes[0]!='U' ||
         disk.bytes.find("TIME=1234 PULSES=4 NONCE=nonce00112233445 TARGET=target0011223344 REASON=window expired\n")==std::string::npos)) ||
       journalRecoveryRequired!=expectRecovery || canAttemptCoinPost()){
      std::cerr<<"SOURCE_QUARANTINE_FAIL scenario="<<scenario<<"\n";
      return 1;
    }
    if(expectRecovery){
      const std::string ambiguousBytes=disk.bytes;
      const int attemptsBeforeRetry=clearCount;
      disk.shortWrite=false;
      disk.verifyOpenFail=false;
      disk.removeOneByteAfterClose=false;
      disk.mutateAfterClose=false;
      disk.mutateOnRead=false;
      clearAllowed=true;
      if(quarantinePending(reason) || disk.bytes!=ambiguousBytes ||
         clearCount!=attemptsBeforeRetry || !journalRecoveryRequired ||
         canAttemptCoinPost()){
        std::cerr<<"SOURCE_QUARANTINE_RETRY_MUTATED scenario="<<scenario<<"\n";
        return 1;
      }
    }
    if(scenario==3 || scenario==4 || (scenario>=5 && scenario<=10) ||
       scenario==11 || scenario==16 || scenario==17 || scenario==18 || scenario==34 || (scenario>=19 && scenario!=31 && scenario!=33)){
      // Simulate volatile latch loss on reboot while retaining LittleFS bytes.
      const std::string rebootBytes=disk.bytes;
      const int clearsBeforeReboot=clearCount;
      journalRecoveryRequired=false;
      disk.hasWritten=false;
      bool rebootOk=quarantinePending(reason);
      bool persistentHardStop=(scenario==3 || scenario==4 || scenario==5 ||
                                scenario==7 || scenario==8 || scenario==10 || scenario==16 || scenario==17 || scenario==18 || scenario==34 || (scenario>=19 && scenario!=31 && scenario!=33));
      if(persistentHardStop){
        if(rebootOk || !journalRecoveryRequired || disk.bytes!=rebootBytes ||
           clearCount!=clearsBeforeReboot || pendingPulses!=4 || canAttemptCoinPost()){
          std::cerr<<"SOURCE_QUARANTINE_TORN_REBOOT_FAIL scenario="<<scenario<<"\n";
          return 1;
        }
      } else {
        if(!rebootOk || journalRecoveryRequired || disk.bytes!=rebootBytes ||
           clearCount!=clearsBeforeReboot+1 || pendingPulses!=0 || canAttemptCoinPost()){
          std::cerr<<"SOURCE_QUARANTINE_IDEMPOTENT_REBOOT_FAIL scenario="<<scenario<<"\n";
          return 1;
        }
      }
    }
  }
  std::cout<<"SOURCE_QUARANTINE_PASS 36/36 scenarios (physical power cut NOT tested)\n";
}
'''
