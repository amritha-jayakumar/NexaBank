const fs = require('fs');
const htmlhint = require('htmlhint').HTMLHint;
const html = fs.readFileSync('templates/admin_dashboard.html', 'utf8');
const messages = htmlhint.verify(html, htmlhint.defaultRuleset);
messages.forEach(m => console.log(`Line ${m.line}: ${m.message}`));
