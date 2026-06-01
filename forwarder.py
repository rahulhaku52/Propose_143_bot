import os

print("BOT_TOKEN =", os.environ.get("BOT_TOKEN"))
print("CHANNEL_IDS =", os.environ.get("CHANNEL_IDS"))
exit()
import os, json, requests, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_IDS = os.environ['CHANNEL_IDS'].split(',')  # একাধিক চ্যানেল
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
        return {}

def save_last_id(data):
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f)

def get_new_groups_via_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        resp = requests.get(url, timeout=10).json()
        new_ids = []
        if resp.get('ok'):
            for update in resp['result']:
                if 'my_chat_member' in update:
                    chat = update['my_chat_member']['chat']
                    if chat['type'] in ['group', 'supergroup']:
                        new_ids.append(chat['id'])
                elif 'message' in update:
                    chat = update['message']['chat']
                    if chat['type'] in ['group', 'supergroup']:
                        if chat['id'] not in new_ids:
                            new_ids.append(chat['id'])
        return new_ids
    except Exception as e:
        print(f"⚠️ getUpdates error: {e}")
        return []

def get_latest_channel_posts():
    """সব চ্যানেলের সর্বশেষ পোস্ট চেক"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    posts = {}
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get('ok'):
            for update in reversed(resp['result']):
                if 'channel_post' in update:
                    chat_id = str(update['channel_post']['chat']['id'])
                    msg_id = update['channel_post']['message_id']
                    if chat_id not in posts:
                        posts[chat_id] = msg_id
        return posts
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return {}

def forward_to_group(chat_id, from_chat, message_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/forwardMessage"
    payload = {
        "chat_id": chat_id,
        "from_chat_id": from_chat,
        "message_id": message_id
    }
    resp = requests.post(url, json=payload, timeout=10).json()
    return resp.get('ok')

def git_save():
    try:
        subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", GROUPS_FILE, LOG_FILE], check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if diff.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Update"], check=True)
            subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("✅ Git saved")
    except Exception as e:
        print(f"⚠️ Git error: {e}")

def main():
    print("🔍 Checking new groups...")
    groups = load_groups()
    
    new_ids = get_new_groups_via_updates()
    for gid in new_ids:
        if gid not in groups:
            groups.append(gid)
            print(f"✅ New group: {gid}")
    
    if new_ids:
        save_groups(groups)
    
    print(f"📋 Groups: {len(groups)}")
    
    if not groups:
        print("ℹ️  No groups yet.")
        return
    
    # সব চ্যানেলের পোস্ট চেক
    latest_posts = get_latest_channel_posts()
    if not latest_posts:
        print("ℹ️  No channel posts.")
        return
    
    last_ids = load_last_id()
    total_forwarded = 0
    
    for channel_id in CHANNEL_IDS:
        # channel_id ইউজারনেম হলে getUpdates থেকে chat_id বের করা
        # এখানে আমরা সরাসরি ইউজারনেম ব্যবহার করব
        for chat_id_str, msg_id in latest_posts.items():
            last_for_channel = last_ids.get(channel_id, 0)
            if msg_id > last_for_channel:
                print(f"📤 {channel_id}: msg {msg_id}")
                for gid in groups:
                    ok = forward_to_group(gid, channel_id, msg_id)
                    if ok:
                        total_forwarded += 1
                last_ids[channel_id] = msg_id
    
    if total_forwarded > 0:
        save_last_id(last_ids)
        print(f"🎯 Forwarded {total_forwarded} messages")
        git_save()
    else:
        print("ℹ️  No new posts.")

if __name__ == "__main__":
    main()
