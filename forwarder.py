import os
import json
import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_IDS = [x.strip() for x in os.environ["CHANNEL_IDS"].split(",")]

GROUPS_FILE = "groups.json"
LOG_FILE = "last_forwarded_id.json"

def load_groups():
    try:
        with open(GROUPS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def load_last_ids():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                return {}
    except Exception:
        return {}

def save_last_ids(data):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def get_updates():
    allowed = ["message", "channel_post"]
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=100&allowed_updates={json.dumps(allowed)}"
    response = requests.get(url, timeout=20)
    return response.json()

def forward_message(group_id, from_chat_id, message_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/forwardMessage"

    payload = {
        "chat_id": group_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id
    }

    response = requests.post(url, json=payload, timeout=20).json()

    print(f"➡️ {group_id} => {response}")

    return response.get("ok", False)

def main():
    groups = load_groups()

    print(f"📋 Loaded groups: {groups}")

    updates = get_updates()

    print(json.dumps(updates, indent=2, ensure_ascii=False))

    posts = {}

    for update in updates.get("result", []):

        # ==========================
        # CHANNEL POSTS
        # ==========================
        if "channel_post" in update:
            channel_id = str(update["channel_post"]["chat"]["id"])
            message_id = update["channel_post"]["message_id"]
            posts[channel_id] = message_id
            print(f"📢 Found channel post: {channel_id} -> {message_id}")

        # ==========================
        # REGULAR GROUP MESSAGES
        # ==========================
        elif "message" in update:
            msg = update["message"]
            chat_id = str(msg["chat"]["id"])
            message_id = msg["message_id"]

            # শুধু গ্রুপ/সুপারগ্রুপ থেকে আসা মেসেজ ফরওয়ার্ড করো (প্রাইভেট মেসেজ স্কিপ)
            if msg["chat"]["type"] in ["group", "supergroup"]:
                # সোর্স চ্যাট আইডি হিসেবে গ্রুপের আইডি ব্যবহার করো
                # কিন্তু তুমি চাইলে শুধু নির্দিষ্ট সোর্স থেকেই ফরওয়ার্ড করতে পারো
                if chat_id in CHANNEL_IDS:
                    posts[chat_id] = message_id
                    print(f"📢 Found group message: {chat_id} -> {message_id}")

    if not posts:
        print("ℹ️ No posts to forward")
        return

    last_ids = load_last_ids()

    total_forwarded = 0

    for channel_id in CHANNEL_IDS:

        if channel_id not in posts:
            continue

        message_id = posts[channel_id]

        last_message_id = last_ids.get(channel_id, 0)

        if message_id <= last_message_id:
            continue

        for group_id in groups:

            # নিজে নিজে ফরওয়ার্ড এড়িয়ে যাও (যেন লুপ না হয়)
            if group_id == channel_id:
                continue

            if forward_message(group_id, channel_id, message_id):
                total_forwarded += 1

        last_ids[channel_id] = message_id

    save_last_ids(last_ids)

    print(f"🎯 Forwarded: {total_forwarded}")

if __name__ == "__main__":
    main()
