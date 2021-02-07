let child = require('child_process');

let p = child.spawnSync('python3', ['-m', 'django', 'version'])
console.log(p.stdout.toString('utf8'))

