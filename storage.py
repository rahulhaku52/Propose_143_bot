import json
import os

GROUPS_FILE = "groups.json"
STATE_FILE = "state.json"

# ─────────────────────────────────────────
# GROUPS - Read / Write
# ─────────────────────────────────────────

def load_groups():
    """সব গ্রুপ ID লোড করো"""
    if not os.path.exists(GROUPS_FILE):
        return []
    with open(GROUPS_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_group(chat_id):
    """নতুন গ্রুপ ID save করো (duplicate এড়িয়ে)"""
    groups = load_groups()
    if chat_id not in groups:
        groups.append(chat_id)
        with open(GROUPS_FILE, "w") as f:
            json.dump(groups, f, indent=2)
        print(f"✅ New group saved: {chat_id}")
    else:
        print(f"ℹ️ Group already exists: {chat_id}")

def remove_group(chat_id):
    """গ্রুপ remove করো (bot kicked হলে)"""
    groups = load_groups()
    if chat_id in groups:
        groups.remove(chat_id)
        with open(GROUPS_FILE, "w") as f:
            json.dump(groups, f, indent=2)
        print(f"🗑️ Group removed: {chat_id}")

# ─────────────────────────────────────────
# STATE - Last Message ID
# ─────────────────────────────────────────

def load_last_message_id():
    """শেষ forward করা message ID লোড করো"""
    if not os.path.exists(STATE_FILE):
        return 0
    with open(STATE_FILE, "r") as f:
        try:
            data = json.load(f)
            return data.get("last_message_id", 0)
        except:
            return 0

def save_last_message_id(message_id):
    """শেষ forward করা message ID save করো"""
    with open(STATE_FILE, "w") as f:
        json.dump({"last_message_id": message_id}, f, indent=2)
    print(f"💾 Last message ID saved: {message_id}")
