import asyncio
import os
import time
from telegram import Bot
from telegram.error import TelegramError
from storage import load_groups, load_last_message_id, save_last_message_id

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Multiple Channel IDs (comma separated)
CHANNEL_IDS_RAW = os.environ.get("CHANNEL_IDS", "")
CHANNEL_IDS = [c.strip() for c in CHANNEL_IDS_RAW.split(",") if c.strip()]

DELAY_BETWEEN_GROUPS = 30
DELAY_BETWEEN_CHANNELS = 10  # 🆕: Channel switch এর সময়

# ─────────────────────────────────────────
# File check
# ─────────────────────────────────────────
def ensure_files_exist():
    if not os.path.exists("groups.json"):
        with open("groups.json", "w") as f:
            f.write("[]")
    if not os.path.exists("state.json"):
        with open("state.json", "w") as f:
            f.write('{"last_message_id": 0}')

# ─────────────────────────────────────────
# Get new messages from ALL channels
# ─────────────────────────────────────────
async def get_all_new_messages(bot: Bot):
    """সব Channel থেকে নতুন Post সংগ্রহ করো"""
    all_new_messages = []
    
    print(f"\n📡 Checking {len(CHANNEL_IDS)} channels...")
    
    for channel_id in CHANNEL_IDS:
        print(f"\n🔍 Checking channel: {channel_id}")
        
        # Per-channel state (আমরা সব channel এর জন্য আলাদা রাখতে পারি)
        # আপাতত: সব channel থেকে নতুন post নেব
        
        try:
            # Check if bot has access
            try:
                chat = await bot.get_chat(chat_id=channel_id)
                print(f"✅ Channel found: {chat.title}")
            except:
                print(f"❌ Cannot access channel: {channel_id}")
                continue
            
            # Get updates
            updates = await bot.get_updates(limit=100, allowed_updates=["channel_post"])
            
            for update in updates:
                if update.channel_post:
                    msg = update.channel_post
                    if str(msg.chat.id) == str(channel_id):
                        all_new_messages.append({
                            "message": msg,
                            "channel_id": channel_id
                        })
                        print(f"📄 Found post ID: {msg.message_id} from {channel_id}")
        
        except Exception as e:
            print(f"❌ Error with channel {channel_id}: {e}")
    
    # Sort by message ID
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
        
        # Delay between groups
        if i < len(groups):
            await asyncio.sleep(DELAY_BETWEEN_GROUPS)
    
    print(f"📊 Result: ✅ {success_count} success | ❌ {fail_count} failed")

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    print("🚀 Multi-Channel Forwarder Started!")
    
    # Check config
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set!")
        return
    
    if not CHANNEL_IDS:
        print("❌ No CHANNEL_IDS configured!")
        print("💡 Add CHANNEL_IDS to GitHub Secrets (comma separated)")
        print("   Example: -1001234567890,-1009876543210")
        return
    
    print(f"📡 Total channels: {len(CHANNEL_IDS)}")
    print(f"📡 Channels: {CHANNEL_IDS}")
    
    # Ensure files
    ensure_files_exist()
    
    # Load groups
    groups = load_groups()
    if not groups:
        print("⚠️ No groups found! Add bot to groups first.")
        return
    
    print(f"📋 Loaded {len(groups)} groups")
    
    # Initialize bot
    bot = Bot(token=BOT_TOKEN)
    
    # Get all new messages from all channels
    all_new = await get_all_new_messages(bot)
    
    if not all_new:
        print("\n💤 No new messages found in any channel.")
        return
    
    # Forward each message
    for item in all_new:
        await forward_to_groups(
            bot=bot,
            message=item["message"],
            channel_id=item["channel_id"],
            groups=groups
        )
        
        # Short delay between different channels' messages
        await asyncio.sleep(DELAY_BETWEEN_CHANNELS)
    
    print("\n✅ All channels processed!")

if __name__ == "__main__":
    asyncio.run(main())
