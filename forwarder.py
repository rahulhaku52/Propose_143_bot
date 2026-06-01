import os
import json
import requests
import subprocess

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_IDS = [x.strip() for x in os.environ["CHANNEL_IDS"].split(",")]

GROUPS_FILE = "groups.json"
LOG_FILE = "last_forwarded_id.json"

def load_groups():
try:
with open(GROUPS_FILE, "r") as f:
groups = json.load(f)
print(f"📋 Loaded groups: {groups}")
return groups
except:
return []

def save_groups(groups):
with open(GROUPS_FILE, "w") as f:
json.dump(groups, f)

def load_last_ids():
try:
with open(LOG_FILE, "r") as f:
return json.load(f)
except:
return {}

def save_last_ids(data):
with open(LOG_FILE, "w") as f:
json.dump(data, f)

def get_updates():
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=100"

```
try:
    resp = requests.get(url, timeout=20).json()

    print("========== UPDATES ==========")
    print(json.dumps(resp, indent=2))
    print("=============================")

    return resp

except Exception as e:
    print(f"⚠️ getUpdates error: {e}")
    return {"ok": False}
```

def detect_new_groups(resp):
groups = []

```
if not resp.get("ok"):
    return groups

for update in resp["result"]:

    if "my_chat_member" in update:
        chat = update["my_chat_member"]["chat"]

        if chat["type"] in ["group", "supergroup"]:
            groups.append(chat["id"])

    elif "message" in update:
        chat = update["message"]["chat"]

        if chat["type"] in ["group", "supergroup"]:
            groups.append(chat["id"])

return list(set(groups))
```

def detect_channel_posts(resp):
posts = {}

```
if not resp.get("ok"):
    return posts

for update in resp["result"]:

    if "channel_post" not in update:
        continue

    post = update["channel_post"]

    chat_id = str(post["chat"]["id"])
    message_id = post["message_id"]

    print(f"📢 Channel Post Found")
    print(f"📢 Channel ID: {chat_id}")
    print(f"📢 Message ID: {message_id}")

    posts[chat_id] = message_id

return posts
```

def forward_message(group_id, channel_id, message_id):
url = f"https://api.telegram.org/bot{BOT_TOKEN}/forwardMessage"

```
payload = {
    "chat_id": group_id,
    "from_chat_id": channel_id,
    "message_id": message_id
}

r = requests.post(url, json=payload, timeout=20).json()

print(f"➡️ {group_id} => {r}")

return r.get("ok", False)
```

def git_save():
try:
subprocess.run(
["git", "config", "user.name", "GitHub Actions"],
check=True
)

```
    subprocess.run(
        ["git", "config", "user.email", "actions@github.com"],
        check=True
    )

    subprocess.run(
        ["git", "add", GROUPS_FILE, LOG_FILE],
        check=True
    )

    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"]
    )

    if diff.returncode != 0:
        subprocess.run(
            ["git", "commit", "-m", "Auto update"],
            check=True
        )

        subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            check=True
        )

        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True
        )

except Exception as e:
    print(f"⚠️ Git error: {e}")
```

def main():

```
groups = load_groups()

updates = get_updates()

new_groups = detect_new_groups(updates)

changed = False

for gid in new_groups:
    if gid not in groups:
        groups.append(gid)
        changed = True
        print(f"✅ New group added: {gid}")

if changed:
    save_groups(groups)

print(f"📋 Total groups: {len(groups)}")

if not groups:
    print("❌ No groups found")
    return

posts = detect_channel_posts(updates)

if not posts:
    print("ℹ️ No channel posts")
    return

last_ids = load_last_ids()

total = 0

for channel_id in CHANNEL_IDS:

    if channel_id not in posts:
        continue

    msg_id = posts[channel_id]

    last_msg = last_ids.get(channel_id, 0)

    if msg_id <= last_msg:
        continue

    for gid in groups:

        if forward_message(gid, channel_id, msg_id):
            total += 1

    last_ids[channel_id] = msg_id

save_last_ids(last_ids)

print(f"🎯 Forwarded: {total}")

git_save()
```

if **name** == "**main**":
main()
