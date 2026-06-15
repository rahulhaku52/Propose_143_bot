import asyncio
import os
import json
from telegram import Bot
from telegram.error import TelegramError

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # 🔐 GitHub Secret

# 📢 আপনার ৩টি Channel ID:
CHANNEL_IDS = [
    "-1003824167133",  # RealTalkSexEd
    "-1003946427531",  # Sexy_Shortss
    "-1002520786250",  # Xauusd_125
]

DELAY_BETWEEN_GROUPS   = 2   # ১০ থেকে ২ সেকেন্ড
DELAY_BETWEEN_CHANNELS = 2   # ৫ থেকে ২ সেকেন্ড

# ─────────────────────────────────────────
# File Functions
# ─────────────────────────────────────────
def load_groups():
    if not os.path.exists("groups.json"):
        return []
    with open("groups.json", "r") as f:
        try:
            return json.load(f)
        except:
            return []

def load_state():
    if not os.path.exists("state.json"):
        return {}
    with open("state.json", "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_state(state):
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)

def ensure_files():
    if not os.path.exists("groups.json"):
        with open("groups.json", "w") as f:
            json.dump([], f)
        print("📁 Created groups.json")

    if not os.path.exists("state.json"):
        with open("state.json", "w") as f:
            json.dump({}, f)
        print("📁 Created state.json")

    print("✅ Files ready!")

# ─────────────────────────────────────────
# Get New Messages
# ─────────────────────────────────────────
async def get_new_messages(bot: Bot, channel_id: str, last_id: int):
    new_messages = []

    try:
        # Channel access check
        chat = await bot.get_chat(chat_id=channel_id)
        print(f"  ✅ Channel: {chat.title}")

        # Get updates
        updates = await bot.get_updates(
            limit=100,
            allowed_updates=["channel_post"]
        )

        for update in updates:
            if update.channel_post:
                msg = update.channel_post
                if str(msg.chat.id) == str(channel_id):
                    if msg.message_id > last_id:
                        new_messages.append(msg)
                        print(f"  🆕 New post: ID {msg.message_id}")
                    else:
                        print(f"  ⏭️ Old post: ID {msg.message_id} (skip)")

    except Exception as e:
        print(f"  ❌ Error: {e}")

    new_messages.sort(key=lambda m: m.message_id)
    return new_messages

# ─────────────────────────────────────────
# Forward to Groups
# ─────────────────────────────────────────
async def forward_to_groups(bot: Bot, message, channel_id: str, groups: list):
    success = 0
    failed  = 0

    print(f"\n  📤 Forwarding to {len(groups)} groups...")

    for i, group_id in enumerate(groups, 1):
        try:
            await bot.forward_message(
                chat_id      = group_id,
                from_chat_id = channel_id,
                message_id   = message.message_id,
            )
            print(f"    ✅ [{i}/{len(groups)}] → {group_id}")
            success += 1

        except TelegramError as e:
            err = str(e).lower()
            print(f"    ❌ [{i}/{len(groups)}] → {group_id} | {e}")
            failed += 1

            # Invalid group হলে remove করো
            if any(x in err for x in ["kicked", "not found", "blocked", "deactivated"]):
                groups_data = load_groups()
                if group_id in groups_data:
                    groups_data.remove(group_id)
                    with open("groups.json", "w") as f:
                        json.dump(groups_data, f, indent=2)
                    print(f"    🗑️ Removed invalid group: {group_id}")

        if i < len(groups):
            await asyncio.sleep(DELAY_BETWEEN_GROUPS)

    print(f"\n  📊 ✅ {success} success | ❌ {failed} failed")

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    print("=" * 50)
    print("🚀 Telegram Auto Forwarder Started!")
    print("=" * 50)

    # Check Token
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set in GitHub Secrets!")
        return

    print(f"✅ Token: {BOT_TOKEN[:10]}...")
    print(f"📡 Channels: {len(CHANNEL_IDS)}")

    # Ensure files
    ensure_files()

    # Load groups
    groups = load_groups()
    if not groups:
        print("⚠️ No groups found!")
        return
    print(f"👥 Groups: {len(groups)}")

    # Init bot
    bot = Bot(token=BOT_TOKEN)

    # Load state (per channel last message ID)
    state = load_state()
    print(f"📌 State: {state}")

    total_forwarded = 0

    # Process each channel
    for ch_idx, channel_id in enumerate(CHANNEL_IDS, 1):
        print(f"\n{'='*50}")
        print(f"📡 Channel {ch_idx}/{len(CHANNEL_IDS)}: {channel_id}")
        print(f"{'='*50}")

        # Per channel last ID
        last_id = state.get(channel_id, 0)
        print(f"📌 Last ID for this channel: {last_id}")

        # Get new messages
        new_msgs = await get_new_messages(bot, channel_id, last_id)

        if not new_msgs:
            print(f"💤 No new messages in {channel_id}")
            continue

        print(f"🆕 Found {len(new_msgs)} new message(s)!")

        # Forward each message
        for msg in new_msgs:
            print(f"\n📨 Message ID: {msg.message_id}")

            await forward_to_groups(
                bot        = bot,
                message    = msg,
                channel_id = channel_id,
                groups     = groups,
            )

            # Update state
            state[channel_id] = msg.message_id
            save_state(state)
            total_forwarded += 1

        # Delay between channels
        if ch_idx < len(CHANNEL_IDS):
            print(f"\n⏳ Waiting {DELAY_BETWEEN_CHANNELS}s before next channel...")
            await asyncio.sleep(DELAY_BETWEEN_CHANNELS)

    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Done!")
    print(f"📊 Forwarded: {total_forwarded} message(s)")
    print(f"👥 To: {len(groups)} groups")
    print(f"📡 From: {len(CHANNEL_IDS)} channel(s)")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())
