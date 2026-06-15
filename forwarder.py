import asyncio
import os
import time
from telegram import Bot
from telegram.error import TelegramError
from storage import (
    load_groups,
    load_last_message_id,
    save_last_message_id,
)

# ─────────────────────────────────────────
# CONFIG (GitHub Secrets থেকে আসবে)
# ─────────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")   # Example: -1001234567890

# প্রতি গ্রুপে forward করার আগে delay (seconds)
DELAY_BETWEEN_GROUPS = 30

# ─────────────────────────────────────────
# নতুন পোস্ট চেক করো
# ─────────────────────────────────────────
async def get_new_messages(bot: Bot, last_id: int):
    """Channel থেকে নতুন পোস্ট নিয়ে আসো"""
    new_messages = []

    try:
        # Channel এর সব messages এর মধ্যে নতুনগুলো খোঁজো
        # Telegram API limit: 100 per call
        updates = await bot.get_updates(limit=100, allowed_updates=["channel_post"])

        for update in updates:
            if update.channel_post:
                msg = update.channel_post
                # শুধু আমাদের channel এর পোস্ট
                if str(msg.chat.id) == str(CHANNEL_ID):
                    if msg.message_id > last_id:
                        new_messages.append(msg)

    except TelegramError as e:
        print(f"❌ Error getting messages: {e}")

    # ID অনুযায়ী sort করো (পুরনো আগে)
    new_messages.sort(key=lambda m: m.message_id)
    return new_messages

# ─────────────────────────────────────────
# সব গ্রুপে Forward করো
# ─────────────────────────────────────────
async def forward_to_groups(bot: Bot, message, groups: list):
    """একটা message সব গ্রুপে forward করো"""

    success_count = 0
    fail_count    = 0
    failed_groups = []

    print(f"\n📤 Forwarding message ID: {message.message_id}")
    print(f"📋 Total groups: {len(groups)}")

    for i, group_id in enumerate(groups, 1):
        try:
            # ✅ Message forward করো
            await bot.forward_message(
                chat_id     = group_id,
                from_chat_id= CHANNEL_ID,
                message_id  = message.message_id,
            )
            print(f"  ✅ [{i}/{len(groups)}] Forwarded to: {group_id}")
            success_count += 1

        except TelegramError as e:
            print(f"  ❌ [{i}/{len(groups)}] Failed for {group_id}: {e}")
            fail_count += 1
            failed_groups.append(group_id)

        # ⏳ প্রতি গ্রুপে delay
        if i < len(groups):
            print(f"  ⏳ Waiting {DELAY_BETWEEN_GROUPS}s before next group...")
            await asyncio.sleep(DELAY_BETWEEN_GROUPS)

    print(f"\n📊 Result: ✅ {success_count} success | ❌ {fail_count} failed")
    return failed_groups

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    print("🚀 Forwarder started...")
    print(f"📡 Channel ID: {CHANNEL_ID}")

    # Bot init করো
    bot = Bot(token=BOT_TOKEN)

    # গ্রুপ লিস্ট লোড করো
    groups = load_groups()
    if not groups:
        print("⚠️ No groups found in groups.json!")
        print("💡 Add bot to groups first using bot.py")
        return

    print(f"📋 Loaded {len(groups)} groups")

    # শেষ message ID লোড করো
    last_id = load_last_message_id()
    print(f"📌 Last forwarded message ID: {last_id}")

    # নতুন পোস্ট খোঁজো
    new_messages = await get_new_messages(bot, last_id)

    if not new_messages:
        print("💤 No new messages to forward.")
        return

    print(f"🆕 Found {len(new_messages)} new message(s)!")

    # প্রতিটা নতুন পোস্ট forward করো
    for message in new_messages:
        failed = await forward_to_groups(bot, message, groups)

        # State update করো
        save_last_message_id(message.message_id)

        # অল্প বিরতি দাও পরের message এর আগে
        if message != new_messages[-1]:
            await asyncio.sleep(5)

    print("\n✅ All done!")

if __name__ == "__main__":
    asyncio.run(main())
