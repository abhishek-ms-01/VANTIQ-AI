import asyncio
from notifications import check_and_send_alert

async def run():
    # Construct a mock trade plan that bypasses validation just to prove the notification works
    plan = {
        "direction": "LONG",
        "entry_price": 4415.00,
        "stop_loss": 4402.00,
        "target_1": 4438.40,
        "signal_strength": 99,
        "regime": "BULL",
        "session_tier": "NEW_YORK",
        "signal_type": "BREAKOUT"
    }
    
    print("Sending mock trade alert to Telegram...")
    check_and_send_alert(plan)
    
    # give async tasks a moment to fire
    await asyncio.sleep(2)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(run())
