import os, json, requests, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']  # যে চ্যানেল থেকে ফরওয়ার্ড হবে
GROUPS_FILE = "groups.json"
LOG_FILE = "last_forwarded_id.json"

def load_groups():
    try:
        with open(GROUPS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_groups(groups):
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f)

def load_last_id():
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return 0

def save_last_id(msg_id):
    with open(LOG_FILE, 'w') as f:
        json.dump(msg_id, f)

def get_new_groups_via_updates():
    """getUpdates দিয়ে নতুন গ্রুপের ID সংগ্রহ (যখন বট অ্যাড হবে)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        resp = requests.get(url, timeout=10).json()
        new_ids = []
        if resp.get('ok'):
            for update in resp['result']:
                # গ্রুপ বা সুপারগ্রুপে বট অ্যাড হলে
                if 'my_chat_member' in update:
                    chat = update['my_chat_member']['chat']
                    if chat['type'] in ['group', 'supergroup']:
                        new_ids.append(chat['id'])
                # অথবা মেসেজের মাধ্যমে গ্রুপ ID
                elif 'message' in update:
                    chat = update['message']['chat']
                    if chat['type'] in ['group', 'supergroup']:
                        if chat['id'] not in new_ids:
                            new_ids.append(chat['id'])
        return new_ids
    except Exception as e:
        print(f"⚠️ getUpdates error: {e}")
        return []

def get_latest_channel_post():
    """চ্যানেলের সর্বশেষ পোস্টের message_id বের করা"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('ok'):
            # চ্যানেল পোস্ট খোঁজা
            for update in reversed(resp['result']):
                if 'channel_post' in update:
                    return update['channel_post']['message_id']
        return None
    except Exception as e:
        print(f"⚠️ Channel post check error: {e}")
        return None

def forward_to_group(chat_id, from_chat, message_id):
    """একটা গ্রুপে মেসেজ ফরওয়ার্ড করা"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/forwardMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat,
        "message_id": message_id
    }
    resp = requests.post(url, json=payload, timeout=10).json()
    return resp.get('ok')

def git_save():
    """groups.json গিটে সেভ করা"""
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", GROUPS_FILE, LOG_FILE], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update groups/log"], check=True)
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Git saved")
    except Exception as e:
        print(f"⚠️ Git error: {e}")

def main():
    print("🔍 Checking new groups...")
    groups = load_groups()
    
    # নতুন গ্রুপ অ্যাড হয়েছে কিনা চেক
    new_ids = get_new_groups_via_updates()
    for gid in new_ids:
        if gid not in groups:
            groups.append(gid)
            print(f"✅ New group added: {gid}")
    
    if new_ids:
        save_groups(groups)
    
    print(f"📋 Total groups: {len(groups)}")
    
    if not groups:
        print("ℹ️  No groups yet. Waiting...")
        return
    
    # চ্যানেলের সর্বশেষ পোস্ট চেক
    latest_msg = get_latest_channel_post()
    if not latest_msg:
        print("ℹ️  No channel post found.")
        return
    
    last_id = load_last_id()
    if latest_msg <= last_id:
        print(f"ℹ️  Already forwarded (last: {last_id}, latest: {latest_msg})")
        return
    
    print(f"📤 Forwarding message {latest_msg} to {len(groups)} groups...")
    
    # চ্যানেলের ইউজারনেম বা আইডি থেকে from_chat বের করা
    # CHANNEL_ID যদি @username হয়, তাহলে সেটাই ব্যবহার হবে
    from_chat = CHANNEL_ID
    
    success = 0
    for gid in groups:
        ok = forward_to_group(gid, from_chat, latest_msg)
        if ok:
            success += 1
            print(f"  ✅ Forwarded to {gid}")
        else:
            print(f"  ❌ Failed: {gid}")
    
    save_last_id(latest_msg)
    print(f"🎯 Forwarded to {success}/{len(groups)} groups")
    
    # Git save
    git_save()

if __name__ == "__main__":
    main()
