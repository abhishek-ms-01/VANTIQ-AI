import httpx
import asyncio
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8867639803:AAFbEoa0eBlbtVNO6Pnb6PT8GyYwjGY3Ek8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629588889")

_last_notified_regime = None

def check_and_send_alert(strategy_data):
    global _last_notified_regime
    
    if not strategy_data or 'direction' not in strategy_data:
        return
        
    direction = strategy_data['direction']
    score = strategy_data.get('signal_strength', strategy_data.get('score', 0))
    regime = strategy_data.get('regime', 'UNKNOWN')
    
    sig_id = f"{direction}_{regime}"
    
    # Notify if we get a LONG or SHORT signal
    if direction in ['LONG', 'SHORT']:
        if sig_id != _last_notified_regime:
            
            def fmt(val):
                return f"{float(val):.3f}" if isinstance(val, (int, float)) else str(val)

            emoji = "🟢" if direction == 'LONG' else "🔴"
            action = "BUY" if direction == 'LONG' else "SELL"
            
            entry = strategy_data.get('entry', strategy_data.get('entry_price'))
            sl = strategy_data.get('stop_loss')
            tp = strategy_data.get('target_1')
            session = strategy_data.get('session_tier', 'UNKNOWN').replace("_", " ")
            setup_type = strategy_data.get('signal_type', 'STANDARD')
            
            message = (
                f"⚡ *VANTIQ {setup_type} EXECUTION* ⚡\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"*{emoji} ACTION:* {action} GOLD (XAU/USD)\n"
                f"🔹 *Entry Price:* {fmt(entry)}\n"
                f"🔹 *Take Profit:* {fmt(tp)}\n"
                f"🔹 *Stop Loss:* {fmt(sl)}\n\n"
                f"📊 *Context:* {session} Session\n"
                f"🎯 *Confidence:* {score}%\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🌐 [Open VANTIQ Terminal](https://vantiq-ai-l4ba.vercel.app/)"
            )
            
            # Fire and forget async request
            asyncio.create_task(_send_async(message))
            _last_notified_regime = sig_id
            
    # Reset notification lock if market goes back to neutral/no trade
    elif direction == 'NO_TRADE':
        _last_notified_regime = None

async def _send_async(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, timeout=5.0)
    except Exception as e:
        print(f"Telegram notification failed: {e}")
