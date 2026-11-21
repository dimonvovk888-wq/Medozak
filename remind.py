import json, os, urllib.request
from datetime import datetime, timedelta, timezone

vl_tz = timezone(timedelta(hours=10))
tomorrow = (datetime.now(vl_tz) + timedelta(days=1)).strftime("%d.%m")

with open("schedule.json", encoding="utf-8") as f:
    data = json.load(f)

items = data.get(tomorrow, [])
if not items:
    print(f"На {tomorrow} заданий нет — ничего не отправляем.")
    raise SystemExit(0)

lines = [f"📌 <b>Напоминание: что сдать завтра ({tomorrow})</b>\n"]
for item in items:
    lines.append(f"• <b>{item['subject']}</b>")
    for task in item["tasks"]:
        lines.append(f"  — {task}")

payload = {
    "chat_id": os.environ["CHAT_ID"],
    "message_thread_id": int(os.environ["TOPIC_ID"]),
    "text": "\n".join(lines),
    "parse_mode": "HTML"
}

url = f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendMessage"
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    print("Отправлено:", resp.status)
