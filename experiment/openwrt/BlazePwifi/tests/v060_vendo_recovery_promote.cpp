// CTRL-20261023-RESTORE: host fake-LittleFS durability/error injection.
// Only tests promotion of validated pending-event recovery candidates.
#include <cassert>
#include <cstring>
#include <iostream>
#include "../esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h"

struct FakeStore {
    bool dat = false;
    bool next = false;
    bool backup = false;
    bool deny_remove = false;
    bool deny_rename = false;
    int removals = 0;
    int renames = 0;

    bool exists(const char *name) const {
        if (!std::strcmp(name, "/pending.dat")) return dat;
        if (!std::strcmp(name, "/pending.new")) return next;
        if (!std::strcmp(name, "/pending.bak")) return backup;
        return false;
    }
    bool remove(const char *name) {
        assert(!std::strcmp(name, "/pending.dat"));
        ++removals;
        if (deny_remove || !dat) return false;
        dat = false;
        return true;
    }
    bool rename(const char *source, const char *destination) {
        ++renames;
        assert(!std::strcmp(destination, "/pending.dat"));
        if (deny_rename || dat || !exists(source)) return false;
        if (!std::strcmp(source, "/pending.new")) next = false;
        else if (!std::strcmp(source, "/pending.bak")) backup = false;
        else return false;
        dat = true;
        return true;
    }
};

int main() {
    // Canonical valid record requires no destructive writes.
    FakeStore canonical; canonical.dat = true;
    assert(bp_pending_promote_recovered(canonical, "/pending.dat"));
    assert(canonical.dat && canonical.removals == 0 && canonical.renames == 0);
    FakeStore missing_canonical;
    assert(!bp_pending_promote_recovered(missing_canonical, "/pending.dat"));

    // Recovery from interrupted write / old backup with missing canonical.
    FakeStore newly_written; newly_written.next = true;
    assert(bp_pending_promote_recovered(newly_written, "/pending.new"));
    assert(newly_written.dat && !newly_written.next);
    FakeStore backed_up; backed_up.backup = true;
    assert(bp_pending_promote_recovered(backed_up, "/pending.bak"));
    assert(backed_up.dat && !backed_up.backup);

    // Corrupt canonical removal fails: do not ACK, delete or rename.
    FakeStore remove_fails; remove_fails.dat = true; remove_fails.next = true;
    remove_fails.deny_remove = true;
    assert(!bp_pending_promote_recovered(remove_fails, "/pending.new"));
    assert(remove_fails.dat && remove_fails.next && remove_fails.renames == 0);

    // Rename fails after old invalid canonical removed. Keep recovery source.
    FakeStore rename_fails; rename_fails.dat = true; rename_fails.next = true;
    rename_fails.deny_rename = true;
    assert(!bp_pending_promote_recovered(rename_fails, "/pending.new"));
    assert(!rename_fails.dat && rename_fails.next);

    // Recovery backup must be retained if its rename fails.
    FakeStore backup_fails; backup_fails.backup = true; backup_fails.deny_rename = true;
    assert(!bp_pending_promote_recovered(backup_fails, "/pending.bak"));
    assert(backup_fails.backup && !backup_fails.dat);

    // Do not delete canonical state on missing or unrecognized request.
    FakeStore invalid; invalid.dat = true;
    assert(!bp_pending_promote_recovered(invalid, "/pending.new"));
    assert(!bp_pending_promote_recovered(invalid, "/pending.stranger"));
    assert(!bp_pending_promote_recovered(invalid, nullptr));
    assert(invalid.dat && invalid.removals == 0 && invalid.renames == 0);

    std::cout << "CTRL-RESTORE fake LittleFS promotions and failure handling PASS\n";
}
