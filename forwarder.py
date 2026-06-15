import os
import logging
import asyncio
from telegram import Bot
from storage import load_groups, load_state, save_state

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')  # যেমন: @your_channel বা -100123456789
DELAY_SECONDS = int(os.getenv('DELAY_SECONDS', 30))  # Default 30 সেকেন্ড
TAG_TEXT = os.getenv('TAG_TEXT', '📢 আমাদের চ্যানেল থেকে')

async def forward_new_posts():
    """চ্যানেলের নতুন পোস্ট সব গ্রুপে forward করে"""
    bot = Bot(token=BOT_TOKEN)
    groups = load_groups()
    state = load_state()
    
    if not groups:
        logger.warning("⚠️ কোনো গ্রুপ নেই। bot.py দিয়ে গ্রুপ add করুন।")
        return
    
    try:
        # চ্যানেলের সর্বশেষ পোস্ট পেতে (আপনার চ্যানেল থেকে)
        # এখানে আমরা ধরে নিচ্ছি আপনি message_id manually দিচ্ছেন বা API দিয়ে latest fetch করছেন
        # সহজ উদাহরণ: আপনি latest 10টা message চেক করবেন
        
        # আপনার চ্যানেলের latest message ID (এটা আপনাকে logic করতে হবে)
        # উদাহরণ: getUpdates বা channel থেকে latest message
        
        # সরলীকৃত: ধরে নিচ্ছি আপনি শেষ message_id জানেন
        last_forwarded = state.get('last_message_id', 0)
        
        # Example: manually increment (আসল প্রজেক্টে channel থেকে fetch করবেন)
        # এখানে demo logic — আপনি এটা replace করবেন
        
        # চ্যানেল থেকে নতুন পোস্ট চেক করতে:
        # আপনাকে channel message history fetch করতে হবে
        # এটা একটা example — actual implementation আপনার channel access অনুযায়ী
        
        # Placeholder: ধরি নতুন message আছে ID = last_forwarded + 1
        new_message_id = last_forwarded + 1  # আপনি actual logic দেবেন
        
        logger.info(f"📨 নতুন পোস্ট forward করছি: Message ID {new_message_id}")
        
        success_count = 0
        fail_count = 0
        
        for group_id in groups:
            try:
                # Forward message with caption/tag
                await bot.forward_message(
                    chat_id=group_id,
                    from_chat_id=CHANNEL_ID,
                    message_id=new_message_id
                )
                
                # Optional: tag পাঠান (আলাদা message হিসেবে)
                # await bot.send_message(chat_id=group_id, text=TAG_TEXT)
                
                success_count += 1
                logger.info(f"✅ গ্রুপে পাঠানো হয়েছে: {group_id}")
                
                # Delay
                await asyncio.sleep(DELAY_SECONDS)
                
            except Exception as e:
                fail_count += 1
                logger.error(f"❌ গ্রুপে পাঠানো যায়নি {group_id}: {e}")
        
        # State update
        save_state({'last_message_id': new_message_id})
        logger.info(f"🎉 সম্পন্ন: {success_count} সফল, {fail_count} ব্যর্থ")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == '__main__':
    if not BOT_TOKEN or not CHANNEL_ID:
        logger.error("❌ BOT_TOKEN বা CHANNEL_ID নেই!")
    else:
        asyncio.run(forward_new_posts())
