import {archiveThreshold, shouldArchive, mergeMessages, archiveFits} from '/usr/share/blaze/sms-archive-core.uc';

let checks = 0;
function equal(actual, expected, label) {
	checks++;
	if (sprintf('%J', actual) != sprintf('%J', expected))
		die(label + ': expected ' + sprintf('%J', expected) + ', got ' + sprintf('%J', actual));
}

equal(archiveThreshold(35), 30, 'keep five modem slots free');
equal(shouldArchive(29, 35), false, 'do not archive below threshold');
equal(shouldArchive(30, 35), true, 'archive at threshold');
equal(shouldArchive(30, 0), false, 'ignore unknown capacity');

let first = {sender:'639000000001', timestamp:'2026-10-15 10:00:00', index:'1', content:'one'};
let second = {sender:'639000000002', timestamp:'2026-10-15 10:00:01', index:'2', content:'two'};
equal(mergeMessages([first], [first, second]), [first, second], 'deduplicate retries while retaining new messages');
equal(archiveFits(5000, 1000000), true, 'accept archive within limits');
equal(archiveFits(5001, 1000000), false, 'reject archive above message limit');
equal(archiveFits(5000, 1048577), false, 'reject archive above byte limit');

print('PASS: ' + checks + ' SMS archive core checks');
