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
except:
return []

def load_last_ids():
try:
with open(LOG_FILE, "r", encoding="utf-8") as f:
return json.load(f)
except:
return {}

def save_last_ids(data):
with open(LOG_FILE, "w", encoding="utf-8") as f:
json.dump(data, f)

def get_updates():
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?limit=100"
return requests.get(url, timeout=20).json()

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

def main():
groups = load_groups()
print("📋 Groups:", len(groups))

```
updates = get_updates()

print(json.dumps(updates, indent=2))

posts = {}

for update in updates.get("result", []):

    if "channel_post" not in update:
        continue

    channel_id = str(update["channel_post"]["chat"]["id"])
    message_id = update["channel_post"]["message_id"]

    posts[channel_id] = message_id

    print(f"📢 Found post: {channel_id} -> {message_id}")

if not posts:
    print("ℹ️ No channel posts")
    return

last_ids = load_last_ids()

total = 0

for channel_id in CHANNEL_IDS:

    if channel_id not in posts:
        continue

    message_id = posts[channel_id]

    if message_id <= last_ids.get(channel_id, 0):
        continue

    for group_id in groups:
        if forward_message(group_id, channel_id, message_id):
            total += 1

    last_ids[channel_id] = message_id

save_last_ids(last_ids)

print(f"🎯 Forwarded: {total}")
```

if **name** == "**main**":
main()
