import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:lan_messenger/src/compact_call_card.dart';

void main() {
  testWidgets('incoming voice toast exposes both Answer and Decline',
      (tester) async {
    var answer = 0;
    var decline = 0;
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Center(
      child: SizedBox(width: 348, child: CompactCallCard(
        peerName: 'PC-02',
        video: false,
        incoming: true,
        connecting: false,
        muted: false,
        onAnswer: () => answer++,
        onDecline: () => decline++,
        onMute: () {},
        onEnd: () {},
        onOpenThread: () {},
      )),
    ))));
    expect(find.text('PC-02'), findsOneWidget);
    expect(find.text('Incoming voice call'), findsOneWidget);
    expect(find.byKey(const Key('answer-call')), findsOneWidget);
    expect(find.byKey(const Key('decline-call')), findsOneWidget);
    await tester.tap(find.byKey(const Key('answer-call')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('decline-call')));
    expect(answer, 1);
    expect(decline, 1);
    expect(find.byKey(const Key('mute-call')), findsNothing);
  });

  testWidgets('active call stays compact with mute, end and thread actions',
      (tester) async {
    final actions = <String>[];
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Center(
      child: SizedBox(width: 348, child: CompactCallCard(
        peerName: 'ANDROID-02',
        video: false,
        incoming: false,
        connecting: false,
        muted: false,
        onAnswer: () {},
        onDecline: () {},
        onMute: () => actions.add('mute'),
        onEnd: () => actions.add('end'),
        onOpenThread: () => actions.add('thread'),
      )),
    ))));
    expect(find.text('Voice call in progress'), findsOneWidget);
    expect(find.byKey(const Key('answer-call')), findsNothing);
    await tester.tap(find.byKey(const Key('mute-call')));
    await tester.tap(find.byKey(const Key('open-thread')));
    await tester.tap(find.byKey(const Key('end-call')));
    expect(actions, ['mute', 'thread', 'end']);
  });

  testWidgets('incoming video call keeps two explicit response buttons',
      (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: Center(
      child: SizedBox(width: 348, child: CompactCallCard(
        peerName: 'PC-03',
        video: true,
        incoming: true,
        connecting: true,
        muted: false,
        onAnswer: () {},
        onDecline: () {},
        onMute: () {},
        onEnd: () {},
        onOpenThread: () {},
      )),
    ))));
    expect(find.text('Incoming video call'), findsOneWidget);
    expect(find.text('Answer'), findsOneWidget);
    expect(find.text('Decline'), findsOneWidget);
  });
}
