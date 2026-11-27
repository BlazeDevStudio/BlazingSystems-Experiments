#include <cstdint>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <string>

struct BpPendingSequence {
    uint32_t magic;
    uint16_t version;
    uint16_t reserved;
    uint64_t acked_sequence;
    uint64_t sequence;
    uint8_t pulses;
    char nonce[17];
    char target[33];
    uint32_t checksum;
};

bool pendingSequenceValid = true;
bool bp_pending_sequence_valid(const BpPendingSequence *state) {
    return pendingSequenceValid && state != nullptr;
}

struct FakeLittleFS;

class File {
public:
    File() = default;
    File(FakeLittleFS *fs, const char *path, bool valid)
        : fs_(fs), path_(path ? path : ""), valid_(valid) {}
    explicit operator bool() const { return valid_; }
    size_t write(const uint8_t *data, size_t size);
    void flush();
    void close();
private:
    FakeLittleFS *fs_ = nullptr;
    std::string path_;
    bool valid_ = false;
};

struct FakeLittleFS {
    bool dat = false;
    bool fresh = false;
    bool backup = false;
    std::string datBytes;
    std::string freshBytes;
    std::string backupBytes;

    bool failOpen = false;
    bool failShortWrite = false;
    bool failRemoveBackup = false;
    bool failRemoveNew = false;
    bool failRenameDatToBackup = false;
    bool failRenameNewToDat = false;
    bool failRestoreBackup = false;
    bool failFinalBackupRemove = false;
    bool corruptFullWrite = false;
    bool failReadbackOpen = false;
    bool failReadbackShort = false;
    bool corruptReadback = false;

    int openCalls = 0;
    int writeCalls = 0;
    int flushCalls = 0;
    int closeCalls = 0;
    int removeCalls = 0;
    int renameCalls = 0;

    bool exists(const char *path) const {
        if (std::strcmp(path, "/pending.dat") == 0) return dat;
        if (std::strcmp(path, "/pending.new") == 0) return fresh;
        if (std::strcmp(path, "/pending.bak") == 0) return backup;
        return false;
    }

    File open(const char *path, const char *mode) {
        ++openCalls;
        if (failOpen || std::strcmp(path, "/pending.new") != 0 ||
            std::strcmp(mode, "w") != 0) return File();
        fresh = true;
        freshBytes.clear();
        return File(this, path, true);
    }

    size_t writeFile(const char *path, const uint8_t *data, size_t size) {
        ++writeCalls;
        if (std::strcmp(path, "/pending.new") != 0 || !fresh) return 0;
        const size_t written = failShortWrite && size > 0 ? size - 1 : size;
        freshBytes.assign(reinterpret_cast<const char *>(data), written);
        if (corruptFullWrite && written == size && !freshBytes.empty()) {
            freshBytes[0] = static_cast<char>(freshBytes[0] ^ 0x01);
        }
        return written;
    }

    void flushFile(const char *path) {
        if (std::strcmp(path, "/pending.new") == 0) ++flushCalls;
    }

    void closeFile(const char *path) {
        if (std::strcmp(path, "/pending.new") == 0) ++closeCalls;
    }

    bool remove(const char *path) {
        ++removeCalls;
        if (std::strcmp(path, "/pending.new") == 0) {
            if (!fresh || failRemoveNew) return false;
            fresh = false;
            freshBytes.clear();
            return true;
        }
        if (std::strcmp(path, "/pending.bak") == 0) {
            if (!backup) return false;
            if (failRemoveBackup && fresh) return false;
            if (failFinalBackupRemove && dat && !fresh) return false;
            backup = false;
            backupBytes.clear();
            return true;
        }
        return false;
    }

    bool rename(const char *from, const char *to) {
        ++renameCalls;
        if (std::strcmp(from, "/pending.dat") == 0 &&
            std::strcmp(to, "/pending.bak") == 0) {
            if (failRenameDatToBackup || !dat || backup) return false;
            backup = true;
            backupBytes = datBytes;
            dat = false;
            datBytes.clear();
            return true;
        }
        if (std::strcmp(from, "/pending.new") == 0 &&
            std::strcmp(to, "/pending.dat") == 0) {
            if (failRenameNewToDat || !fresh || dat) return false;
            dat = true;
            datBytes = freshBytes;
            fresh = false;
            freshBytes.clear();
            return true;
        }
        if (std::strcmp(from, "/pending.bak") == 0 &&
            std::strcmp(to, "/pending.dat") == 0) {
            if (failRestoreBackup || !backup || dat) return false;
            dat = true;
            datBytes = backupBytes;
            backup = false;
            backupBytes.clear();
            return true;
        }
        return false;
    }
};

size_t File::write(const uint8_t *data, size_t size) {
    return valid_ && fs_ ? fs_->writeFile(path_.c_str(), data, size) : 0;
}
void File::flush() {
    if (valid_ && fs_) fs_->flushFile(path_.c_str());
}
void File::close() {
    if (valid_ && fs_) fs_->closeFile(path_.c_str());
}

struct FakeSerial {
    int calls = 0;
    std::string last;
    void println(const char *message) { ++calls; last = message ? message : ""; }
} Serial;

FakeLittleFS LittleFS;
bool fsReady = true;
BpPendingSequence pendingSequenceState{
    0x42505632UL, 2, 0, 0, 1, 1, "AAAAAAAAAAAAAAAA", "00000001", 0
};

bool readPendingFile(const char *path, BpPendingSequence &state, bool &legacy) {
    if (std::strcmp(path, "/pending.new") != 0 || !LittleFS.fresh ||
        LittleFS.failReadbackOpen || LittleFS.failReadbackShort ||
        LittleFS.freshBytes.size() != sizeof(state)) return false;
    std::memcpy(&state, LittleFS.freshBytes.data(), sizeof(state));
    if (LittleFS.corruptReadback) ++state.sequence;
    legacy = false;
    return bp_pending_sequence_valid(&state);
}

/*__PERSIST_PENDING_SEQUENCE_FUNCTION__*/

static BpPendingSequence nextState() {
    return BpPendingSequence{
        0x42505632UL, 2, 0, 1, 2, 4, "BBBBBBBBBBBBBBBB", "00000002", 0
    };
}

static bool oldRamStateUnchanged() {
    return pendingSequenceState.sequence == 1 &&
           pendingSequenceState.pulses == 1 &&
           std::strcmp(pendingSequenceState.nonce, "AAAAAAAAAAAAAAAA") == 0;
}

static void resetState() {
    LittleFS = FakeLittleFS{};
    Serial = FakeSerial{};
    fsReady = true;
    pendingSequenceValid = true;
    pendingSequenceState = BpPendingSequence{
        0x42505632UL, 2, 0, 0, 1, 1, "AAAAAAAAAAAAAAAA", "00000001", 0
    };
}

static bool promotedStateMatches(const BpPendingSequence &state) {
    return LittleFS.dat && !LittleFS.fresh && !LittleFS.backup &&
           LittleFS.datBytes.size() == sizeof(state) &&
           std::memcmp(LittleFS.datBytes.data(), &state, sizeof(state)) == 0 &&
           pendingSequenceState.sequence == state.sequence &&
           pendingSequenceState.pulses == state.pulses;
}

int main() {
    int scenarios = 0;
    BpPendingSequence next = nextState();

    resetState();
    if (!persistPendingSequence(next) || !promotedStateMatches(next) ||
        LittleFS.flushCalls != 1 || LittleFS.renameCalls != 1) return 1;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    if (!persistPendingSequence(next) || !promotedStateMatches(next) ||
        LittleFS.renameCalls != 2) return 2;
    ++scenarios;

    resetState();
    LittleFS.failOpen = true;
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    if (persistPendingSequence(next) || !LittleFS.dat || LittleFS.fresh ||
        !oldRamStateUnchanged()) return 3;
    ++scenarios;

    resetState();
    pendingSequenceValid = false;
    if (persistPendingSequence(next) || LittleFS.openCalls != 0 ||
        !oldRamStateUnchanged()) return 4;
    ++scenarios;

    resetState();
    fsReady = false;
    if (persistPendingSequence(next) || LittleFS.openCalls != 0 ||
        !oldRamStateUnchanged()) return 5;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failShortWrite = true;
    if (persistPendingSequence(next) || !LittleFS.dat || LittleFS.fresh ||
        !oldRamStateUnchanged() || LittleFS.removeCalls != 1) return 6;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failShortWrite = true;
    LittleFS.failRemoveNew = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        !oldRamStateUnchanged()) return 7;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.backup = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.backupBytes = "older-backup";
    LittleFS.failRemoveBackup = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        !LittleFS.backup || LittleFS.renameCalls != 0 ||
        Serial.calls != 1 || !oldRamStateUnchanged()) return 8;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failRenameDatToBackup = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        LittleFS.backup || LittleFS.renameCalls != 1 ||
        Serial.calls != 1 || !oldRamStateUnchanged()) return 9;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failRenameNewToDat = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        LittleFS.backup || LittleFS.renameCalls != 3 ||
        Serial.calls != 1 || !oldRamStateUnchanged()) return 10;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failRenameNewToDat = true;
    LittleFS.failRestoreBackup = true;
    if (persistPendingSequence(next) || LittleFS.dat || !LittleFS.fresh ||
        !LittleFS.backup || LittleFS.renameCalls != 3 ||
        Serial.calls != 2 || !oldRamStateUnchanged()) return 11;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failFinalBackupRemove = true;
    if (persistPendingSequence(next) || !LittleFS.dat || LittleFS.fresh ||
        !LittleFS.backup || LittleFS.renameCalls != 2 ||
        Serial.calls != 1 || !oldRamStateUnchanged()) return 12;
    ++scenarios;

    resetState();
    LittleFS.backup = true;
    LittleFS.backupBytes = "old-backup";
    if (!persistPendingSequence(next) || !promotedStateMatches(next) ||
        LittleFS.removeCalls != 1 || LittleFS.renameCalls != 1) return 13;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.corruptFullWrite = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        LittleFS.renameCalls != 0 || !oldRamStateUnchanged()) return 14;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failReadbackOpen = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        LittleFS.renameCalls != 0 || !oldRamStateUnchanged()) return 15;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.failReadbackShort = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        LittleFS.renameCalls != 0 || !oldRamStateUnchanged()) return 16;
    ++scenarios;

    resetState();
    LittleFS.dat = true;
    LittleFS.datBytes = "old-canonical";
    LittleFS.corruptReadback = true;
    if (persistPendingSequence(next) || !LittleFS.dat || !LittleFS.fresh ||
        LittleFS.renameCalls != 0 || !oldRamStateUnchanged()) return 17;
    ++scenarios;

    std::cout << "PENDING_PERSIST_FAILURE_PASS scenarios=" << scenarios << "\n";
    return 0;
}
