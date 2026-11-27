
#include <cstdint>
#include <cstring>
#include <iostream>

struct BpPendingSequence {
    uint32_t sequence;
    uint8_t pulses;
    char nonce[17];
    char target[33];
};

class String {
public:
    String() = default;
    String(const char *value) : value_(value ? value : "") {}
private:
    const char *value_ = "";
};

struct FakeLittleFS {
    bool dat = false;
    bool fresh = false;
    bool backup = false;
    bool failRename = false;
    int renameCalls = 0;

    bool exists(const char *path) const {
        if (std::strcmp(path, "/pending.dat") == 0) return dat;
        if (std::strcmp(path, "/pending.new") == 0) return fresh;
        if (std::strcmp(path, "/pending.bak") == 0) return backup;
        return false;
    }

    bool rename(const char *from, const char *to) {
        ++renameCalls;
        if (failRename) return false;
        bool *source = slot(from);
        bool *destination = slot(to);
        if (!source || !destination || !*source || *destination) return false;
        *source = false;
        *destination = true;
        return true;
    }

private:
    bool *slot(const char *path) {
        if (std::strcmp(path, "/pending.dat") == 0) return &dat;
        if (std::strcmp(path, "/pending.new") == 0) return &fresh;
        if (std::strcmp(path, "/pending.bak") == 0) return &backup;
        return nullptr;
    }
} LittleFS;

struct FakeSerial {
    void println(const char *) {}
} Serial;

bool fsReady = true;
bool pendingReady = false;
uint8_t pendingPulses = 0;
uint32_t lastSend = 99;
BpPendingSequence pendingSequenceState{};
String pendingNonce;
String pendingTarget;
const char *selectedPath = nullptr;
bool selectedLegacy = false;
bool persistOk = true;
int persistCalls = 0;

bool readPendingFile(const char *path, BpPendingSequence &state, bool &legacy) {
    if (!LittleFS.exists(path) || !selectedPath ||
        std::strcmp(path, selectedPath) != 0) return false;
    state.sequence = 9;
    state.pulses = 3;
    std::strcpy(state.nonce, "AABBCCDDEEFF0011");
    std::strcpy(state.target, "00112233");
    legacy = selectedLegacy;
    return true;
}

void bp_pending_sequence_init(BpPendingSequence *state) {
    std::memset(state, 0, sizeof(*state));
}

bool persistPendingSequence(const BpPendingSequence &) {
    ++persistCalls;
    if (!persistOk) return false;
    LittleFS.dat = true;
    return true;
}

/*__LOAD_PENDING_FUNCTION__*/

static void resetState() {
    LittleFS = FakeLittleFS{};
    fsReady = true;
    pendingReady = false;
    pendingPulses = 0;
    lastSend = 99;
    pendingSequenceState = BpPendingSequence{};
    pendingNonce = String();
    pendingTarget = String();
    selectedPath = nullptr;
    selectedLegacy = false;
    persistOk = true;
    persistCalls = 0;
}

int main() {
    resetState();
    LittleFS.dat = true;
    selectedPath = "/pending.dat";
    if (!loadPending() || !fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || LittleFS.renameCalls != 0) return 1;

    resetState();
    LittleFS.fresh = true;
    selectedPath = "/pending.new";
    if (!loadPending() || !fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || !LittleFS.dat ||
        LittleFS.fresh || LittleFS.renameCalls != 1) return 2;

    resetState();
    LittleFS.backup = true;
    selectedPath = "/pending.bak";
    if (!loadPending() || !fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || !LittleFS.dat ||
        LittleFS.backup || LittleFS.renameCalls != 1) return 3;

    resetState();
    LittleFS.dat = true;
    LittleFS.fresh = true;
    selectedPath = "/pending.new";
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.dat || !LittleFS.fresh ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 0) return 4;

    resetState();
    LittleFS.dat = true;
    LittleFS.backup = true;
    selectedPath = "/pending.bak";
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.dat || !LittleFS.backup ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 0) return 5;

    resetState();
    LittleFS.fresh = true;
    selectedPath = "/pending.new";
    LittleFS.failRename = true;
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.fresh || LittleFS.dat ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 1) return 6;

    resetState();
    LittleFS.backup = true;
    selectedPath = "/pending.bak";
    LittleFS.failRename = true;
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.backup || LittleFS.dat ||
        pendingSequenceState.sequence != 0 || LittleFS.renameCalls != 1) return 7;

    resetState();
    LittleFS.dat = true;
    if (loadPending() || fsReady || !pendingReady ||
        !LittleFS.dat || pendingSequenceState.sequence != 0) return 8;

    resetState();
    if (!loadPending() || !fsReady || !LittleFS.dat ||
        pendingSequenceState.sequence != 0 || persistCalls != 1) return 9;

    resetState();
    persistOk = false;
    if (loadPending() || fsReady || !pendingReady ||
        LittleFS.dat || persistCalls != 1) return 10;

    resetState();
    LittleFS.dat = true;
    selectedPath = "/pending.dat";
    selectedLegacy = true;
    persistOk = false;
    if (loadPending() || fsReady || !pendingReady ||
        pendingSequenceState.sequence != 9 || !LittleFS.dat ||
        persistCalls != 1) return 11;

    std::cout << "PENDING_RECOVERY_PROMOTION_PASS scenarios=11 rename_failures=2 ambiguous_preservation=2\n";
    return 0;
}
