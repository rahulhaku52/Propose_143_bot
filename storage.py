import json
import os

GROUPS_FILE = 'groups.json'
STATE_FILE = 'state.json'

def load_groups():
    """সব গ্রুপ ID লোড করে"""
    if not os.path.exists(GROUPS_FILE):
        return []
    with open(GROUPS_FILE, 'r') as f:
        return json.load(f)

def save_groups(groups):
    """গ্রুপ ID save করে"""
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f, indent=2)

def add_group(chat_id):
    """নতুন গ্রুপ add করে (duplicate এড়িয়ে)"""
    groups = load_groups()
    if chat_id not in groups:
        groups.append(chat_id)
        save_groups(groups)
        return True
    return False

def remove_group(chat_id):
    """গ্রুপ remove করে"""
    groups = load_groups()
    if chat_id in groups:
        groups.remove(chat_id)
        save_groups(groups)
        return True
    return False

def load_state():
    """শেষ পোস্ট ID লোড করে"""
    if not os.path.exists(STATE_FILE):
        return {'last_message_id': 0}
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    """শেষ পোস্ট ID save করে"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
