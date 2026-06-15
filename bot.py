import os
import logging
from telegram import Update
from telegram.ext import Application, ChatMemberHandler, ContextTypes
from storage import add_group, remove_group

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot কে গ্রুপে add/remove করলে track করে"""
    result = update.my_chat_member
    chat = update.effective_chat
    
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    
    # Bot কে গ্রুপে add করলে
    if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator']:
        if chat.type in ['group', 'supergroup']:
            if add_group(chat.id):
                logger.info(f"✅ নতুন গ্রুপ যোগ: {chat.title} (ID: {chat.id})")
    
    # Bot কে গ্রুপ থেকে remove করলে
    elif old_status in ['member', 'administrator'] and new_status in ['left', 'kicked']:
        if remove_group(chat.id):
            logger.info(f"❌ গ্রুপ সরানো: {chat.title} (ID: {chat.id})")

def main():
    """Bot চালু করে"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN পাওয়া যায়নি! .env ফাইল চেক করুন।")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Group add/remove listener
    app.add_handler(ChatMemberHandler(track_groups, ChatMemberHandler.MY_CHAT_MEMBER))
    
    logger.info("🤖 Bot চলছে... গ্রুপে add করুন!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
