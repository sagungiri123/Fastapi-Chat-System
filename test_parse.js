const fs = require('fs');
const content = fs.readFileSync('app/static/index.html', 'utf-8');
const scriptMatch = content.match(/<script>([\s\S]*?)<\/script>/);
if (scriptMatch) {
  try {
    new Function(scriptMatch[1]);
    console.log("Script parsed successfully!");
  } catch (e) {
    console.error("Syntax Error:", e);
  }
} else {
  console.log("No script found.");
}
