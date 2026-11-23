import json
import os
import re
import urllib.request
from pathlib import Path

MATERIALS_DIR = Path("materials")
INDEX_FILE = MATERIALS_DIR / "index.json"
STATE_FILE = MATERIALS_DIR / "sync_state.json"

# Формат команды в тексте или подписи к фото/аудио:
# /k 25.11 ВВИН [необязательный текст конспекта]
CMD_RE = re.compile(r"^/[kк](?:@\w+)?\s+(\d{2}\.\d{2})\s+([^\s\n]+)(?:\s+([\s\S]+))?$", re.IGNORECASE)


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
    query = ""
    if params:
        query = "?" + "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://api.telegram.org/bot{token}/{method}{query}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


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
    slug = re.sub(r"[^a-zA-Z0-9а-яА-ЯёЁ_-]+", "_", text).strip("_")
    return slug or "item"


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

    # Запоминаем тег для альбомов (media_group_id), чтобы все фото из одной пачки попали в нужную пару
    album_tags: dict[str, tuple[str, str]] = {}
    added_count = 0

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

        # 1. Текст конспекта
        if extra_text:
            entry["text"] = (entry["text"] + "\n\n" + extra_text).strip() if entry["text"] else extra_text
            added_count += 1

        # 2. Фото слайда
        if msg.get("photo"):
            best = msg["photo"][-1]
            fname = f"slide_{len(entry['photos']) + 1:02d}_{uid}.jpg"
            dest = folder / fname
            if download_tg_file(token, best["file_id"], dest):
                entry["photos"].append({"name": fname, "url": dest.as_posix()})
                added_count += 1

        # 3. Аудио / голосовое
        audio_obj = msg.get("audio") or msg.get("voice")
        if audio_obj:
            ext = ".ogg" if msg.get("voice") else Path(audio_obj.get("file_name", "audio.mp3")).suffix or ".mp3"
            orig_name = audio_obj.get("file_name") or f"audio_{len(entry['audio']) + 1:02d}{ext}"
            fname = f"audio_{len(entry['audio']) + 1:02d}_{uid}{ext}"
            dest = folder / fname
            if download_tg_file(token, audio_obj["file_id"], dest):
                entry["audio"].append({"name": orig_name, "url": dest.as_posix()})
                added_count += 1

        # 4. Документ (если отправили фото/аудио «без сжатия»)
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
                    added_count += 1
            elif mime.startswith("audio/"):
                fname = f"audio_{len(entry['audio']) + 1:02d}_{uid}{ext or '.mp3'}"
                dest = folder / fname
                if download_tg_file(token, doc["file_id"], dest):
                    entry["audio"].append({"name": orig_name, "url": dest.as_posix()})
                    added_count += 1

    save_json(STATE_FILE, state)
    save_json(INDEX_FILE, index)
    print(f"Готово. Новых материалов добавлено: {added_count}")


if __name__ == "__main__":
    main()
