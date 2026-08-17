const token="8867639803:AAFbEoa0eBlbtVNO6Pnb6PT8GyYwjGY3Ek8";
const chatId="1629588889";
const msg=`🚨 VANTIQ AI TRADE ALERT 🚨

🟢 LONG GOLD
Quality Score: 92/100
Session: HIGH_VOLATILITY (New York)
Action: BUY/LONG
Entry: 2415.50
Stop Loss: 2412.00
Take Profit: 2422.50

Open your Terminal: https://vantiq-ai.vercel.app/`;

fetch("https://api.telegram.org/bot" + token + "/sendMessage", {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({chat_id: chatId, text: msg})
}).then(r=>r.json()).then(console.log).catch(console.error);
