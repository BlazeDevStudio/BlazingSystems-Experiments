import {readfile,writefile,rename,unlink} from 'fs';
import {quote,exec,readjson} from '/usr/share/blaze/common.uc';
import {shouldArchive,mergeMessages,archiveFits} from '/usr/share/blaze/sms-archive-core.uc';

let request = readjson('/tmp/blaze-message.lock/request.json', {});
let storage = request.storage == 'ME' ? 'ME' : 'SM';
let archivePath = '/etc/blaze/sms-inbox-archive.json';

function detectPort() {
	let r = exec('/usr/share/3ginfo-lite/detect.sh 2>/dev/null | head -1');
	let port = trim(r.out || '');
	if (!match(port, /^\/dev\/[A-Za-z0-9._-]+$/)) {
		if (readfile('/sys/class/tty/ttyACM0/dev'))
			port = '/dev/ttyACM0';
		else
			die('No supported modem control port was detected.');
	}
	return port;
}

function modem(port, command, seconds) {
	return exec('/usr/bin/timeout -k 2 ' + seconds + ' /usr/bin/sms_tool -d ' + quote(port) + ' ' + command);
}

function emit(messages, archiveCount, warning) {
	print(sprintf('%J', {
		msg: messages,
		archive_count: archiveCount,
		archive_warning: warning || ''
	}));
}

let port = detectPort();
let inboxResult = modem(port, '-s ' + quote(storage) + ' -f ' + quote('%Y-%m-%d %H:%M:%S') + ' -j recv', 20);
if (inboxResult.rc)
	die(inboxResult.out || 'Could not read modem SMS storage.');

let inbox;
try {
	inbox = json(inboxResult.out);
} catch (e) {
	die('The modem returned invalid inbox data.');
}
if (type(inbox?.msg) != 'array')
	die('The modem returned an unexpected inbox format.');

let current = inbox.msg;
let existing = [], archiveRaw = readfile(archivePath), archiveWarning = '';
if (archiveRaw != null && length(trim(archiveRaw))) {
	try {
		let saved = json(archiveRaw);
		if (saved.version != 1 || type(saved.messages) != 'array')
			die('Invalid archive structure.');
		existing = saved.messages;
	} catch (e) {
		emit(current, 0, 'The saved SMS archive could not be read; modem messages were left untouched.');
		exit(0);
	}
}

let combined = mergeMessages(existing, current);
let cpmsResult = modem(port, "at 'AT+CPMS?'", 10);
let cpms = match(cpmsResult.out || '', /\+CPMS:\s*"[^"]+",[0-9]+,[0-9]+,"[^"]+",[0-9]+,[0-9]+,"[^"]+",[0-9]+,([0-9]+)/);
let capacity = cpms?.[1] ? int(cpms[1]) : 0;

if (!shouldArchive(length(current), capacity)) {
	emit(combined, length(existing), '');
	exit(0);
}

let archivedCurrent = [];
for (let message in current)
	push(archivedCurrent, {...message, archived: true});
combined = mergeMessages(existing, archivedCurrent);

let serialized = sprintf('%J', {version: 1, updated: time(), messages: combined});
if (!archiveFits(length(combined), length(serialized))) {
	emit(combined, length(existing), 'The router SMS archive reached its safe limit. Modem messages were not deleted; download a backup before clearing space.');
	exit(0);
}

if (exec('mkdir -p /etc/blaze && chmod 700 /etc/blaze').rc) {
	emit(combined, length(existing), 'Could not prepare private router storage; modem messages were left untouched.');
	exit(0);
}

let temporary = archivePath + '.new';
if (writefile(temporary, serialized) == null || exec('chmod 600 ' + quote(temporary)).rc) {
	unlink(temporary);
	emit(combined, length(existing), 'Could not write the SMS archive; modem messages were left untouched.');
	exit(0);
}

let verify;
try {
	verify = json(readfile(temporary));
} catch (e) {
	unlink(temporary);
	emit(combined, length(existing), 'The SMS archive could not be verified; modem messages were left untouched.');
	exit(0);
}
if (verify.version != 1 || type(verify.messages) != 'array' || length(verify.messages) != length(combined)) {
	unlink(temporary);
	emit(combined, length(existing), 'The SMS archive verification failed; modem messages were left untouched.');
	exit(0);
}
for (let i = 0; i < length(combined); i++) {
	if (sprintf('%J', verify.messages[i]) != sprintf('%J', combined[i])) {
		unlink(temporary);
		emit(combined, length(existing), 'The SMS archive verification failed; modem messages were left untouched.');
		exit(0);
	}
}
if (!rename(temporary, archivePath)) {
	unlink(temporary);
	emit(combined, length(existing), 'Could not commit the SMS archive; modem messages were left untouched.');
	exit(0);
}

let committed;
try {
	committed = json(readfile(archivePath));
} catch (e) {
	emit(combined, length(existing), 'The committed SMS archive could not be reopened; modem messages were left untouched.');
	exit(0);
}
if (committed.version != 1 || type(committed.messages) != 'array' || length(committed.messages) != length(combined)) {
	emit(combined, length(existing), 'The committed SMS archive failed verification; modem messages were left untouched.');
	exit(0);
}
for (let i = 0; i < length(combined); i++) {
	if (sprintf('%J', committed.messages[i]) != sprintf('%J', combined[i])) {
		emit(combined, length(existing), 'The committed SMS archive failed verification; modem messages were left untouched.');
		exit(0);
	}
}

let deleteResult = modem(port, '-s ' + quote(storage) + ' delete all', 15);
let afterResult = modem(port, '-s ' + quote(storage) + ' -f ' + quote('%Y-%m-%d %H:%M:%S') + ' -j recv', 20);
let after = null;
try { after = json(afterResult.out); } catch (e) {}
if (afterResult.rc || type(after?.msg) != 'array') {
	emit(combined, length(combined), 'The archive is safe, but the modem store could not be rechecked after cleanup.');
	exit(0);
}
if (length(after.msg)) {
	let visible = mergeMessages(combined, after.msg);
	emit(visible, length(combined), 'The archive is saved. New messages arrived during cleanup and remain on the modem.');
	exit(0);
}

if (deleteResult.rc)
	emit(combined, length(combined), 'The archive is safe and the modem store is empty after cleanup.');
else
emit(combined, length(combined), '');
