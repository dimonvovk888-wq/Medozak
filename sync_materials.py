import json
import os
import random
import re
import urllib.request
from pathlib import Path

MATERIALS_DIR = Path("materials")
INDEX_FILE = MATERIALS_DIR / "index.json"
STATE_FILE = MATERIALS_DIR / "sync_state.json"

CMD_RE = re.compile(r"^/[kк](?:@\w+)?\s+(\d{2}\.\d{2})\s+([^\s\n]+)(?:\s+([\s\S]+))?$", re.IGNORECASE)

# 30 вариаций ответа птички-мёдоуказчика после загрузки материалов в конспект
UPLOAD_REPLIES = [
    "🐦🍯 Чик-чик! Всё бережно утащил в соты! В конспект <b>{subject}</b> ({date}) добавлено: {summary} ✅",
    "🐦✨ Чики-чик!! Материалы пойманы на лету! <b>{subject}</b> ({date}) пополнился: {summary} — кнопка «К» уже сияет! 🐝",
    "🐦📦 Чук-чик! Доставка в дупло прошла успешно: в <b>{subject}</b> ({date}) улетело {summary} ✅🍯",
    "🐦💛 Чири-чик! Какие же вы умнички, мёдозвончики! Сохранил для <b>{subject}</b> ({date}): {summary} ✨",
    "🐦🎉 ЧИРИК!! Птенчики хлопают крылышками — в конспект <b>{subject}</b> ({date}) загружено: {summary} ✅🐣",
    "🐦🐝 Бзз-чик! Положил на самую верхнюю полочку улья! <b>{subject}</b> ({date}): {summary} 🍯📚",
    "🐦😌 Чик-чик~ Наконец-то кто-то приносит мёд в наш архив! В <b>{subject}</b> ({date}) добавлено: {summary} ✅",
    "🐦😤 Чирик-чик! Я, конечно, всё загрузил в <b>{subject}</b> ({date}) ({summary}), но где моя награда воском?! 🍯👀",
    "🐦🚀 Чик!! Скорость полёта — максимальная! Материалы для <b>{subject}</b> ({date}) ({summary}) уже в календаре ✅",
    "🐦🕵️ Чик-чик! Проверил клювом, сложил аккуратно: <b>{subject}</b> ({date}) получил {summary} 🔍✨",
    "🐦👑 Чирик-чирик! Архивариус пасеки на связи: <b>{subject}</b> ({date}) обновлён ({summary}) — забирайте корону! 🐝👑",
    "🐦🥺 Чик... Вы реально делитесь конспектами с группой?! Моё птичье сердечко растаяло... <b>{subject}</b> ({date}): {summary} 💛🍯",
    "🐦📚 Чики-чик! К сессии теперь точно выживем! Записал в <b>{subject}</b> ({date}): {summary} ✅🔥",
    "🐦😏 Чик-чик! Ого, работаем красиво: <b>{subject}</b> ({date}) + {summary}. Медведь одобряет! 🐻👍",
    "🐦🌟 Чири-чик!! Звёздочка в карму и ложка мёда автору! В <b>{subject}</b> ({date}) загружено: {summary} 🍯⭐",
    "🐦🔔 Дзынь-чик! Сота заполнена! В разделе «К» у <b>{subject}</b> ({date}) теперь есть: {summary} ✅",
    "🐦🦡 Чик-чик! Мой внутренний медоед в восторге — в <b>{subject}</b> ({date}) приземлилось: {summary} 💛",
    "🐦☕ Чик~ Пока вы пьёте чай, я уже разложил всё по вкладкам! <b>{subject}</b> ({date}): {summary} ✅🍯",
    "🐦📢 Внимание, улей! Чик-чик! Свежий завоз в <b>{subject}</b> ({date}): {summary} — бегом смотреть! 🐝✨",
    "🐦🙃 Чик... Ну хоть кто-то в этой пасеке учится! Загрузил в <b>{subject}</b> ({date}): {summary} ✅😄",
    "🐦🪶 Чири-чик! Аккуратно, пёрышко к пёрышку, сложил в <b>{subject}</b> ({date}): {summary} 🍯📖",
    "🐦🏆 ЧИК-ЧИРИК!! Герой дня найден! Благодаря вам в <b>{subject}</b> ({date}) появилось: {summary} ✅🎉",
    "🐦🌈 Чик-чик~ Пусть на экзамене попадётся самый лёгкий билет! <b>{subject}</b> ({date}) пополнен: {summary} 🍀🐝",
    "🐦⚡ Чик! Молниеносно прикрепил к паре <b>{subject}</b> ({date}): {summary} — открывайте кнопку «К»! ✅",
    "🐦🐱 Чик-чирик! Пчелокотик мурлычет от радости: в <b>{subject}</b> ({date}) добавлено {summary} 🐝💛",
    "🐦🧭 Как верный мёдоуказчик докладываю: маршрут к знаниям по <b>{subject}</b> ({date}) проложен! Загружено: {summary} ✅",
    "🐦💎 Чики-чик! Настоящее золото пасеки! Сохранил в конспект <b>{subject}</b> ({date}): {summary} ✨🍯",
    "🐦🎶 Чири-чик-чик~ Пою победную песню: в <b>{subject}</b> ({date}) успешно уехало {summary} ✅🎵",
    "🐦🤓 Чик! Уровень организованности нашей группы вырос на +100! <b>{subject}</b> ({date}): {summary} 📊🐝",
    "🐦💛 Чик-чик! Спасибо, что кормите календарь материалами! В <b>{subject}</b> ({date}) сохранено: {summary} ✅🍯",
]


def load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def api_get(token: str, method: str, params: dict | None = None) -> dict:
    query = "?" + "&".join(f"{k}={v}" for k, v in params.items()) if params else ""
    url = f"https://api.telegram.org/bot{token}/{method}{query}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_reply(token: str, chat_id: str, text: str, topic_id: int | None = None, reply_to: int | None = None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if topic_id:
        payload["message_thread_id"] = int(topic_id)
    if reply_to:
        payload["reply_to_message_id"] = int(reply_to)
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            print("reply sent:", resp.status)
    except Exception as e:
        print("reply failed:", e)


def download_tg_file(token: str, file_id: str, dest: Path) -> bool:
    info = api_get(token, "getFile", {"file_id": file_id})
    file_path = info.get("result", {}).get("file_path")
    if not file_path:
        return False
    dl_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(dl_url) as resp:
        dest.write_bytes(resp.read())
    return True


def safe_slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ_-]+", "_", text).strip("_") or "item"


def main():
    token = os.environ.get("BOT_TOKEN", "").strip()
    allowed_chat = str(os.environ.get("CHAT_ID", "")).strip()
    if not token:
        print("BOT_TOKEN is empty")
        return

    state = load_json(STATE_FILE, {"last_update_id": 0})
    index = load_json(INDEX_FILE, {})
    offset = int(state.get("last_update_id", 0)) + 1

    res = api_get(token, "getUpdates", {"offset": offset, "timeout": 0})
    updates = res.get("result", [])
    if not updates:
        print("Нет новых сообщений.")
        return

    album_tags: dict[str, tuple[str, str]] = {}
    batch_stats: dict[str, dict] = {}

    for upd in updates:
        uid = int(upd.get("update_id", 0))
        if uid > state["last_update_id"]:
            state["last_update_id"] = uid

        msg = upd.get("message") or upd.get("channel_post")
        if not msg:
            continue

        chat_id = str(msg.get("chat", {}).get("id", ""))
        if allowed_chat and chat_id != allowed_chat:
            continue

        text_or_caption = (msg.get("caption") or msg.get("text") or "").strip()
        mg_id = msg.get("media_group_id")

        match = CMD_RE.match(text_or_caption)
        if match:
            day_str, subj_str, extra_text = match.group(1), match.group(2), (match.group(3) or "").strip()
            if mg_id:
                album_tags[mg_id] = (day_str, subj_str)
        elif mg_id and mg_id in album_tags:
            day_str, subj_str = album_tags[mg_id]
            extra_text = ""
        else:
            continue

        key = f"{day_str}|{subj_str}"
        entry = index.setdefault(key, {"text": "", "audio": [], "photos": []})
        folder = MATERIALS_DIR / f"{day_str.replace('.', '_')}_{safe_slug(subj_str)}"
        st = batch_stats.setdefault(key, {
            "date": day_str, "subject": subj_str, "chat_id": chat_id,
            "topic_id": msg.get("message_thread_id"), "reply_to": msg.get("message_id"),
            "text": 0, "photos": 0, "audio": 0
        })

        if extra_text:
            entry["text"] = (entry["text"] + "\n\n" + extra_text).strip() if entry["text"] else extra_text
            st["text"] += 1

        if msg.get("photo"):
            best = msg["photo"][-1]
            fname = f"slide_{len(entry['photos']) + 1:02d}_{uid}.jpg"
            dest = folder / fname
            if download_tg_file(token, best["file_id"], dest):
                entry["photos"].append({"name": fname, "url": dest.as_posix()})
                st["photos"] += 1

        audio_obj = msg.get("audio") or msg.get("voice")
        if audio_obj:
            ext = ".ogg" if msg.get("voice") else Path(audio_obj.get("file_name", "audio.mp3")).suffix or ".mp3"
            orig_name = audio_obj.get("file_name") or f"audio_{len(entry['audio']) + 1:02d}{ext}"
            fname = f"audio_{len(entry['audio']) + 1:02d}_{uid}{ext}"
            dest = folder / fname
            if download_tg_file(token, audio_obj["file_id"], dest):
                entry["audio"].append({"name": orig_name, "url": dest.as_posix()})
                st["audio"] += 1

        doc = msg.get("document")
        if doc:
            mime = str(doc.get("mime_type", ""))
            orig_name = doc.get("file_name") or f"file_{uid}"
            ext = Path(orig_name).suffix or ""
            if mime.startswith("image/"):
                fname = f"slide_{len(entry['photos']) + 1:02d}_{uid}{ext or '.jpg'}"
                dest = folder / fname
                if download_tg_file(token, doc["file_id"], dest):
                    entry["photos"].append({"name": orig_name, "url": dest.as_posix()})
                    st["photos"] += 1
            elif mime.startswith("audio/"):
                fname = f"audio_{len(entry['audio']) + 1:02d}_{uid}{ext or '.mp3'}"
                dest = folder / fname
                if download_tg_file(token, doc["file_id"], dest):
                    entry["audio"].append({"name": orig_name, "url": dest.as_posix()})
                    st["audio"] += 1

    save_json(STATE_FILE, state)
    save_json(INDEX_FILE, index)

    for st in batch_stats.values():
        parts = []
        if st["text"]:
            parts.append("📝 текст")
        if st["audio"]:
            parts.append(f"🎧 аудио ({st['audio']})")
        if st["photos"]:
            parts.append(f"🖼️ фото ({st['photos']})")
        if not parts:
            continue
        reply_text = random.choice(UPLOAD_REPLIES).format(
            subject=st["subject"],
            date=st["date"],
            summary=", ".join(parts),
        )
        send_reply(token, st["chat_id"], reply_text, st["topic_id"], st["reply_to"])


if __name__ == "__main__":
    main()
