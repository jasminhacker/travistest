child = require('child_process');

test('check', () => {
	let p = child.spawnSync('python3', ['-m', 'django', 'version']);
	console.log(p.stdout.toString('utf8'));
	if (p.error) {
		throw p.error;
	}
	if (p.status != 0) {
		console.error(p.stderr.toString('utf8'));
	}
});
