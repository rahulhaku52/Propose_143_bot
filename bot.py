import asyncio
import os
from telegram import Update
from telegram.ext import (
    Application,
    ChatMemberHandler,
    ContextTypes,
)
from storage import save_group, remove_group

# ─────────────────────────────────────────
# TOKEN (GitHub Secret থেকে আসবে)
# ─────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ─────────────────────────────────────────
# Handler: Bot গ্রুপে ADD / REMOVE হলে
# ─────────────────────────────────────────
async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot গ্রুপে add বা remove হলে auto কাজ করে"""
    result = update.my_chat_member

    # নতুন status
    new_status = result.new_chat_member.status
    chat_id = result.chat.id
    chat_title = result.chat.title

    if new_status in ["member", "administrator"]:
        # ✅ Bot গ্রুপে add হয়েছে
        print(f"➕ Bot added to: {chat_title} ({chat_id})")
        save_group(chat_id)

    elif new_status in ["left", "kicked", "restricted"]:
        # ❌ Bot গ্রুপ থেকে remove হয়েছে
        print(f"➖ Bot removed from: {chat_title} ({chat_id})")
        remove_group(chat_id)

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
async def main():
    print("🤖 Bot started - Listening for group events...")

    app = Application.builder().token(BOT_TOKEN).build()

    # ChatMember handler যোগ করো
    app.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))

    # Bot চালু করো
    await app.run_polling(allowed_updates=["my_chat_member"])

if __name__ == "__main__":
    asyncio.run(main())
