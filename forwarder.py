import asyncio
import os
from telegram import Bot
from telegram.error import TelegramError
from storage import load_groups, load_last_message_id, save_last_message_id

# ─────────────────────────────────────────
# ✅ CONFIG - Token Secret এ, Channel ID Code-এ
# ─────────────────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # 🔐 GitHub Secret থেকে

# 📢 আপনার Channel ID গুলো সরাসরি এখানে দিন
CHANNEL_IDS = [
    "-1001234567890",   # আপনার ১ম Channel
    "-1009876543210",   # আপনার ২য় Channel (যদি থাকে)
    # আরো যোগ করতে পারেন
]

# Time settings
DELAY_BETWEEN_GROUPS = 30      # প্রতি গ্রুপে ৩০ সেকেন্ড delay
DELAY_BETWEEN_CHANNELS = 10    # Channel switch এর সময়

# ─────────────────────────────────────────
# File check
# ─────────────────────────────────────────
def ensure_files_exist():
    """groups.json এবং state.json নিশ্চিত করো"""
    if not os.path.exists("groups.json"):
        with open("groups.json", "w") as f:
            f.write("[]")
        print("📁 Created groups.json")
    
    if not os.path.exists("state.json"):
        with open("state.json", "w") as f:
            f.write('{"last_message_id": 0}')
        print("📁 Created state.json")
    
    print("✅ Files are ready!")

# ─────────────────────────────────────────
# Check new messages from ALL channels
# ─────────────────────────────────────────
async def get_all_new_messages(bot: Bot):
    """সব Channel থেকে নতুন Post সংগ্রহ করো"""
    all_new_messages = []
    
    print(f"\n📡 Checking {len(CHANNEL_IDS)} channels...")
    
    for channel_id in CHANNEL_IDS:
        print(f"\n🔍 Checking channel: {channel_id}")
        
        try:
            # Check if bot has access
            try:
                chat = await bot.get_chat(chat_id=channel_id)
                print(f"✅ Channel found: {chat.title}")
            except Exception as e:
                print(f"❌ Cannot access channel {channel_id}: {e}")
                continue
            
            # Get recent updates
            updates = await bot.get_updates(limit=100, allowed_updates=["channel_post"])
            print(f"📥 Got {len(updates)} updates from Telegram")
            
            for update in updates:
                if update.channel_post:
                    msg = update.channel_post
                    
                    # Check if this message is from our channel
                    if str(msg.chat.id) == str(channel_id):
                        all_new_messages.append({
                            "message": msg,
                            "channel_id": channel_id
                        })
                        print(f"📄 Found post ID: {msg.message_id} from {channel_id}")
        
        except Exception as e:
            print(f"❌ Error with channel {channel_id}: {e}")
    
    # Sort by message ID (oldest first)
    all_new_messages.sort(key=lambda x: x["message"].message_id)
    
    print(f"\n📊 Total new messages from all channels: {len(all_new_messages)}")
    return all_new_messages

# ─────────────────────────────────────────
# Forward to all groups
# ─────────────────────────────────────────
async def forward_to_groups(bot: Bot, message, channel_id, groups: list):
    """একটা message সব গ্রুপে forward করো"""
    
    success_count = 0
    fail_count = 0
    failed_groups = []
    
    print(f"\n📤 Forwarding message ID: {message.message_id} from channel: {channel_id}")
    print(f"📋 Total groups: {len(groups)}")
    
    for i, group_id in enumerate(groups, 1):
        try:
            await bot.forward_message(
                chat_id=group_id,
                from_chat_id=channel_id,
                message_id=message.message_id,
            )
            print(f"  ✅ [{i}/{len(groups)}] Forwarded to: {group_id}")
            success_count += 1
            
        except TelegramError as e:
            print(f"  ❌ [{i}/{len(groups)}] Failed for {group_id}: {e}")
            fail_count += 1
            failed_groups.append(group_id)
        
        # Delay between groups
        if i < len(groups):
            print(f"  ⏳ Waiting {DELAY_BETWEEN_GROUPS}s...")
            await asyncio.sleep(DELAY_BETWEEN_GROUPS)
    
    print(f"\n📊 Result: ✅ {success_count} success | ❌ {fail_count} failed")
    
    if failed_groups:
        print(f"⚠️ Failed groups: {failed_groups}")
    
    return failed_groups

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    print("🚀 Forwarder Started!")
    print("=" * 40)
    
    # Check BOT_TOKEN
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN is not set in GitHub Secrets!")
        print("💡 Add BOT_TOKEN to: GitHub → Settings → Secrets → Actions")
        return
    
    print(f"✅ BOT_TOKEN found (starts with: {BOT_TOKEN[:10]}...)")
    
    # Check channels
    if not CHANNEL_IDS:
        print("❌ No channels configured!")
        print("💡 Add Channel IDs to CHANNEL_IDS list in code")
        return
    
    print(f"📡 Total channels: {len(CHANNEL_IDS)}")
    for i, ch in enumerate(CHANNEL_IDS, 1):
        print(f"   Channel {i}: {ch}")
    
    # Ensure files exist
    ensure_files_exist()
    
    # Load groups
    groups = load_groups()
    if not groups:
        print("⚠️ No groups found in groups.json!")
        print("💡 Add bot to Telegram groups first")
        return
    
    print(f"📋 Loaded {len(groups)} groups")
    
    # Initialize bot
    bot = Bot(token=BOT_TOKEN)
    
    # Get last processed message ID
    last_id = load_last_message_id()
    print(f"📌 Last processed message ID: {last_id}")
    
    # Get new messages from all channels
    all_new = await get_all_new_messages(bot)
    
    if not all_new:
        print("\n💤 No new messages found in any channel.")
        print("💡 Possible reasons:")
        print("   1. No new posts since last check")
        print("   2. Bot is not admin in channel")
        print("   3. Channel ID is incorrect")
        return
    
    print(f"\n🆕 Found {len(all_new)} new message(s)!")
    
    # Forward each message
    for idx, item in enumerate(all_new, 1):
        print(f"\n{'='*40}")
        print(f"📨 Processing message {idx}/{len(all_new)}")
        print(f"{'='*40}")
        
        await forward_to_groups(
            bot=bot,
            message=item["message"],
            channel_id=item["channel_id"],
            groups=groups
        )
        
        # Save progress
        save_last_message_id(item["message"].message_id)
        
        # Delay between channels
        if idx < len(all_new):
            print(f"⏳ Waiting {DELAY_BETWEEN_CHANNELS}s before next channel...")
            await asyncio.sleep(DELAY_BETWEEN_CHANNELS)
    
    print("\n✅ All done! All messages forwarded successfully.")
    print(f"📊 Summary: Processed {len(all_new)} messages across {len(CHANNEL_IDS)} channels")

if __name__ == "__main__":
    asyncio.run(main())
