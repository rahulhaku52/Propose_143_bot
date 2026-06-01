import os, json, requests, subprocess

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_IDS = os.environ['CHANNEL_IDS'].split(',')
GROUPS_FILE = "groups.json"
LOG_FILE = "last_forwarded_id.json"

def load_groups():
    try:
        with open(GROUPS_FILE, 'r') as f:
            groups = json.load(f)
            print(f"📋 Loaded groups: {groups}")
            return groups
    except:
        print("📋 No groups file, starting empty")
        return []

def save_groups(groups):
    with open(GROUPS_FILE, 'w') as f:
        json.dump(groups, f)
    print(f"💾 Saved groups: {groups}")

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
        print(f"🔍 getUpdates response: {json.dumps(resp, indent=2)[:500]}")
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
    print(f"📤 Forwarding: from {from_chat} to {chat_id}, msg {message_id}")
    resp = requests.post(url, json=payload, timeout=10).json()
    print(f"📤 Result: {resp}")
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
    groups = load_groups()
    
    new_ids = get_new_groups_via_updates()
    if new_ids:
        for gid in new_ids:
            if gid not in groups:
                groups.append(gid)
                print(f"✅ New group: {gid}")
        save_groups(groups)
        git_save()
    else:
        print("ℹ️  No new groups in this run.")
    
    print(f"📋 Total groups: {len(groups)}")
    
    if not groups:
        print("ℹ️  No groups. Add bot to group and send /hello")
        return
    
    latest_posts = get_latest_channel_posts()
    if not latest_posts:
        print("ℹ️  No channel posts.")
        return
    
    last_ids = load_last_id()
    forwarded = 0
    
    for ch_id in CHANNEL_IDS:
        ch_id = ch_id.strip()
        for chat_id_str, msg_id in latest_posts.items():
            if str(chat_id_str) != str(ch_id):
                continue
            
            last = last_ids.get(ch_id, 0)
            if msg_id > last:
                print(f"📤 {ch_id}: msg {msg_id}")
                for gid in groups:
                    ok = forward_to_group(gid, ch_id, msg_id)
                    if ok:
                        forwarded += 1
                last_ids[ch_id] = msg_id
    
    if forwarded:
        save_last_id(last_ids)
        print(f"🎯 Forwarded {forwarded} messages")
        git_save()
    else:
        print("ℹ️  No new posts.")

if __name__ == "__main__":
    main()
