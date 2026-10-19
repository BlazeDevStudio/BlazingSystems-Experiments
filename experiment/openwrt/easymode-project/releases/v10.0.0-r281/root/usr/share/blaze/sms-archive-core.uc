function archiveThreshold(capacity) {
	capacity = int(capacity);
	if (capacity <= 0)
		return 0;
	if (capacity <= 5)
		return capacity;
	return capacity - 5 < 30 ? capacity - 5 : 30;
}

function shouldArchive(used, capacity) {
	let threshold = archiveThreshold(capacity);
	return threshold > 0 && int(used) >= threshold;
}

function messageKey(message) {
	return sprintf('%J', [
		'' + (message.sender ?? message.peer ?? message.number ?? ''),
		'' + (message.timestamp ?? message.date ?? ''),
		'' + (message.index ?? ''),
		'' + (message.content ?? message.message ?? message.text ?? '')
	]);
}

function mergeMessages(existing, incoming) {
	let result = [], seen = {};
	for (let rows in [existing, incoming]) {
		if (type(rows) != 'array')
			continue;
		for (let message in rows) {
			if (type(message) != 'object')
				continue;
			let key = messageKey(message);
			if (seen[key])
				continue;
			seen[key] = true;
			push(result, message);
		}
	}
	return result;
}

function archiveFits(messageCount, serializedBytes) {
	return int(messageCount) <= 5000 && int(serializedBytes) <= 1048576;
}

export {archiveThreshold, shouldArchive, mergeMessages, archiveFits};
