import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/group_rooms.dart';

void main() {
  final owner = 'a' * 64;
  final second = 'b' * 64;
  final third = 'c' * 64;
  final outsider = 'd' * 64;
  final roomId = '1' * 32;
  Map<String, dynamic> invite({
    List<String>? members, String? creator, String? id,
  }) => {
    'roomId': id ?? roomId, 'name': 'LAN Friends',
    'creatorId': creator ?? owner, 'members': members ?? [owner, second, third],
  };

  test('three-member encrypted group invite has a valid roster', () {
    final room = GroupRoom.parse(invite(), second, owner);
    expect(room, isNotNull);
    expect(room!.name, 'LAN Friends');
    expect(room.members.length, 3);
    expect(room.accepts(outsider), isFalse);
  });

  test('rejects duplicate members and missing recipients', () {
    expect(GroupRoom.parse(invite(members: [owner, owner, second]),
        second, owner), isNull);
    expect(GroupRoom.parse(invite(), outsider, owner), isNull);
  });

  test('rejects untrusted creator, huge roster and invalid identifiers', () {
    expect(GroupRoom.parse(invite(creator: outsider), second, owner), isNull);
    expect(GroupRoom.parse(invite(members: [
      owner, second, third, outsider, 'e' * 64,
    ]), second, owner), isNull);
    expect(GroupRoom.parse(invite(id: '../..'), second, owner), isNull);
  });

  test('group text deduplicates authenticated sender message IDs', () {
    final room = GroupRoom.parse(invite(), second, owner)!;
    final text = GroupText('m1', owner, 'Hello', DateTime.utc(2026));
    expect(room.addMessage(text), isTrue);
    expect(room.addMessage(text), isFalse);
    expect(room.messages.length, 1);
    expect(room.addMessage(GroupText('m2', outsider, 'fake',
        DateTime.utc(2026))), isFalse);
  });

  test('retains only 300 recent group texts and round trips serialization', () {
    final room = GroupRoom.parse(invite(), second, owner)!;
    for (var i = 0; i < 305; i++) {
      expect(room.addMessage(GroupText('$i', owner, 'hi $i',
          DateTime.utc(2026))), isTrue);
    }
    expect(room.messages.length, 300);
    expect(room.messages.first.text, 'hi 5');
    final saved = room.toJson();
    final loaded = GroupRoom.parse(saved, second, owner);
    expect(loaded!.members, room.members);
    expect(GroupText.fromJson((saved['messages'] as List).last)!.text, 'hi 304');
  });
}
