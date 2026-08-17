import httpx
import asyncio
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8867639803:AAFbEoa0eBlbtVNO6Pnb6PT8GyYwjGY3Ek8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1629588889")

_last_notified_regime = None

def check_and_send_alert(strategy_data):
    global _last_notified_regime
    
    if not strategy_data or 'regime' not in strategy_data:
        return
        
    current_regime = strategy_data['regime']
    score = strategy_data.get('score', 0)
    
    # Only notify if we transition to a strong trade regime (>=65 or <=35)
    # and it's different from the last notified regime to avoid spam
    if current_regime in ['STRONG_BULLISH', 'STRONG_BEARISH']:
        if current_regime != _last_notified_regime:
            
            emoji = "🟢 LONG GOLD" if current_regime == 'STRONG_BULLISH' else "🔴 SHORT GOLD"
            action = "BUY/LONG" if current_regime == 'STRONG_BULLISH' else "SELL/SHORT"
            
            entry = strategy_data.get('entry_price', 'Market')
            sl = strategy_data.get('stop_loss', 'N/A')
            tp = strategy_data.get('target_1', 'N/A')
            
            message = (
                f"🚨 **VANTIQ AI TRADE ALERT** 🚨\n\n"
                f"{emoji}\n"
                f"**Quality Score:** {score}/100\n"
                f"**Action:** {action}\n"
                f"**Entry:** {entry}\n"
                f"**Stop Loss:** {sl}\n"
                f"**Take Profit:** {tp}\n\n"
                f"Open your Terminal: https://vantiq-ai.vercel.app/"
            )
            
            # Fire and forget async request
            asyncio.create_task(_send_async(message))
            _last_notified_regime = current_regime
            
    # Reset notification lock if market goes back to neutral/weak
    elif current_regime in ['NEUTRAL', 'WEAK_BULLISH', 'WEAK_BEARISH']:
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
