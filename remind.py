import json
import mimetypes
import os
import random
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

VL_TZ = timezone(timedelta(hours=10))
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
LAST_MESSAGES_FILE = Path("last_messages.json")

DONE_TEMPLATES = [
    "🐦✨ Чик-чик! Птички щебечут мне, что завтра у вас <b>{subject}</b>! Я конечно же помню, что он уже <b>сдан ✅</b>, но прошу вас, мои мёдозвончики 🍯🔔, проверьте пожалуйста, всё ли вы загрузили, иначе придётся уклоняться от тяжёлой медвежьей лапы... 🐻🐾",
    "🐦🎉 Чики-чик!! <b>{subject}</b> уже на пороге! Птенчики ликуют 🐣✨, ведь разносят весть о том, что он <b>сдан ✅</b> и вы успешно справились с грядущей угрозой, но всё же не стоит расслаБЛЯТЬся! Проверьте, всё ли вы загрузили и подготовили ))))))))) 🍯👀",
    "🐦🐝 Чук-чик!! Медо-барни, кажется угроза <b>{subject}</b> вам завтра не грозит — статус <b>сдан ✅</b>, но всё же напомню вам о ней~ 🍯✨",
    "🐦😤 Чирик-чик-чик!!!!!! Эх.. Раз <b>{subject}</b> у вас давно <b>сдан ✅</b>, могли бы и покормить своего мёдоуказчика лишний раз ) Где мой воск?! 🍯🐝",
    "🐦🌅 Чири-чик! Добрый кхи.. что там у вас на Востоке.. Умнички! Кажется, завтрашний <b>{subject}</b> уже <b>сдан ✅</b>! Посылаю вам всем побольше мёда!!! 🍯💛🐝",
    "🐦🍯 Чик-чирик~ Летел я мимо улья и проверил журнал: <b>{subject}</b> на завтра <b>сдан ✅</b>! Мой внутренний медоед вами гордится, но файл перед сном всё равно перепроверьте 🦡💛",
    "🐦🤨 Чик... Стоп. Вы реально сделали <b>{subject}</b> заранее?! Статус <b>сдан ✅</b>... Подозрительно идеально. Проверьте, не забыли ли вы там титульник, умники мои 🐝📄",
    "🐦🥺 Чик-чик... <b>{subject}</b> уже <b>сдан ✅</b>, и мне даже покричать на вас не за что... Сижу вот один на ветке, клюю пустые соты, никому не нужный мёдоуказчик... 🍂🍯",
    "🐦💃 ЧИРИК!! Барабанная дробь крылышками! <b>{subject}</b> на завтра <b>сдан ✅</b>! Пчелиный совет постановил выдать вам внеочередную порцию мёда и спокойный сон 🐝👑🍯",
    "🐦😏 Чик-чик! Ну надо же, какие мы ответственные: <b>{subject}</b> отмечен как <b>сдан ✅</b>! Только не забудьте завтра прийти на пару, а то обидно будет, медо-барни 👀✨",
    "🐦😮‍💨 Фух, чик... Сердце птичье чуть не остановилось, но вижу: <b>{subject}</b> уже <b>сдан ✅</b>. Продолжайте в том же духе, и я даже не буду наводить на вас медведя 🐻❌🍯",
    "🐦🎺 Чик-чирик! Пасека, внимание! Завтрашний <b>{subject}</b> официально <b>сдан ✅</b>! Можно выдохнуть, попить чай с мёдом и погладить пчелокотика ☕🐱🐝",
    "🐦🙃 Чик... Ну ладно-ладно, <b>{subject}</b> у вас <b>сдан ✅</b>. Я, конечно, рад, просто вы бы видели, как я готовил гневную речь... Зря перья топорщил 🪶😤",
    "🐦🌟 Чирик-чик! Как главный мёдоуказчик этой пасеки докладываю: по предмету <b>{subject}</b> всё чисто, он <b>сдан ✅</b>! Осталось только не забыть флешку/ссылку и забрать свои баллы 🍯💪",
    "🐦🕵️ Чик-чик! Проверил все соты и дупла: <b>{subject}</b> на завтра <b>сдан ✅</b>! Но глаза у меня зоркие — перепроверьте загрузку, чтобы завтра спать спокойно 🐝🔍✨",
]

NOT_DONE_TEMPLATES = [
    "🐦😔 Чик..... <b>{subject}</b>.. уже.. завтра... и он <b>не сдан ❌</b>. . . 🍂",
    "🐦🚨 ЧИК!!!!! И ЧТО ЭТО ТАКОЕ?????? <b>{subject}</b> УЖЕ ЗАВТРА, А ОН <b>НЕ СДАН ❌</b>!!!!!!! ВЫ БУДЕТЕ ЧТО-ТО ДЕЛАТЬ???????? 🐝🔥💢",
    "🐦😟 Чик-чик... <b>{subject}</b> уже завтра, статус <b>не сдан ❌</b>, а вы как будто и не начинали его делать.... Мне уже стоит начинать переживать?... 🍯💧",
    "🐦💀 Чик... Ну всё, расходимся. <b>{subject}</b> завтра, и он до сих пор <b>не сдан ❌</b>. Медведь уже точит лапу, а я даже прикрыть вас не смогу 🐻⚠️",
    "🐦🙃 Чик-чик! Какой прекрасный вечер, чтобы ничего не делать, правда? Вот только завтра <b>{subject}</b>, и он <b>не сдан ❌</b>. Но вы не спешите, у вас же целая ночь впереди))) 🌙☕",
    "🐦😭 Чирик... *всхлип*... Я вам тут мёд ношу, ульи показываю, а <b>{subject}</b> на завтра <b>не сдан ❌</b>... За что вы так с маленькой птичкой... 💔🪶",
    "🐦📢 ТРЕВОГА НА ПАСЕКЕ!! ЧИК-ЧИК-ЧИК!! <b>{subject}</b> завтра, статус <b>не сдан ❌</b>! Бросаем мемы, расправляем крылья и идём спасать зачётку! 🚨🐝⚡",
    "🐦😑 Чик. Смотрю на <b>{subject}</b>. Смотрю на статус <b>не сдан ❌</b>. Смотрю на вас. Молча качаю головой с ветки. Делайте выводы. 🌳👀",
    "🐦🔥 ЧИРИК-ЧИК!! Я мёдоуказчик, а не волшебник — я могу показать дорогу к мёду, но <b>{subject}</b> за вас не напишу! Он всё ещё <b>не сдан ❌</b>, пора шевелить лапками! 🐾🍯",
    "🐦🫠 Чик... Ребята, мёдозвончики мои... Завтра <b>{subject}</b> (<b>не сдан ❌</b>). Если вы планируете делать его в 3 часа ночи — я хотя бы принесу вам воображаемый кофе ☕🦉",
    "🐦😤 Чик-чик! Пассивная агрессия активирована: <b>{subject}</b> на завтра <b>не сдан ❌</b>. Конечно, зачем сдавать вовремя, когда можно словить адреналин перед самой парой, да? 💅🐝",
    "🐦⛈️ Чик... Над нашей секретной пасекой сгущаются тучи. Завтра <b>{subject}</b>, и он всё ещё <b>не сдан ❌</b>. У вас ещё есть шанс всё успеть, не подведите стаю! 🌩️✨",
    "🐦🔔 ДЗЫНЬ-ЧИК!! Последнее птичье предупреждение! <b>{subject}</b> завтра и помечен как <b>не сдан ❌</b>! Открываем ноутбуки и дожимаем до победного! 💻🚀🍯",
]

MORNING_MOTIVATIONS = [
    "🐦☀️ Чик-чирик! Доброе утро, секретная пасека! Птичка-мёдоуказчик уже на посту — расправляйте крылышки и забирайте сегодня весь свой мёд! 🍯🐝",
    "🐦🌅 Чики-чик! Кто рано встаёт, тому медведь соты открывает! Просыпайтесь, мёдозвончики, сегодня мы всех победим! 💪🍯",
    "🐦☕ Чик... Знаю, в 6 утра хочется остаться в дупле под одеялом, но великие дела сами себя не сделают! Глоток кофе — и полетели! 🐝✨",
    "🐦🎺 ЧИРИК!! Подъём, медо-барни! Солнце над Владивостоком встало, пора покорять пары и закрывать хвосты! 🌊☀️",
    "🐦🍯 Чик-чик~ Мёдоуказчик прилетел напомнить: даже если сегодня тяжело, каждый закрытый дедлайн приближает вас к идеальному отдыху! 💛",
    "🐦😤 Чик-чик! Ну что, сонные пчёлки, жужжим или притворяемся мебелью? Встаём, умываемся и рвём этот день! 🐝🔥",
    "🐦🌸 Чири-чик! Пусть сегодняшние пары пролетят быстрее, чем я долетаю до ближайшего улья! Удачи вам, умнички! 🍀🍯",
    "🐦🦉 Чик... Если вы ещё не ложились спать — я вас осуждаю, но всё равно люблю. Держитесь, герои пасеки! 💛☕",
    "🐦🚀 Чик-чирик!! Новый день — новые баллы в зачётку! Помните: вы сильнее любых методичек и дедлайнов! 📚✨",
    "🐦🐻 Чик-чик! Если сегодня будет лень, просто представьте тяжёлую медвежью лапу над зачёткой — сразу появится мотивация! 😄🐾",
    "🐦🐝 Бзз-чик! Пчелиный совет сегодня благосклонен к вам: верю, что хотя бы один крестик ❌ сегодня превратится в галочку ✅! 🍯",
    "🐦🌤️ Чик~ Доброе утро, мои хорошие! Не пытайтесь сделать всё сразу — начните с одного маленького шага, а дальше пойдёт как по мёду! 💛",
    "🐦⚡ ЧИК-ЧИК!! Энергия улья на максимуме! Хватаем тетрадки, хорошее настроение и идём блистать на семинарах! 🌟🐝",
    "🐦🥺 Чирик... Птичка старалась, встала в 6 утра ради вас... Пожалуйста, сделайте сегодня хоть чуть-чуть домашки, чтобы я не грустил 🍯💧",
    "🐦😏 Чик-чик! Доброе утро, легенды ДВФУ! Помните: прокрастинация — это, конечно, искусство, но закрытые дедлайны — роскошь 💅✨",
    "🐦🌿 Чири-чик! Вдох, выдох, глоток чая — и спокойно разбираем задачи. Я в вас верю больше, чем в самый сладкий улей! 🍵🍯",
    "🐦🔔 Чик-дзынь! Утренняя перекличка пасеки! Все живы? Отлично, тогда вперёд навстречу знаниям и высоким баллам! 🐝📚",
    "🐦🎉 Чики-чик!! Сегодня отличный день, чтобы удивить преподавателей и самих себя! Летим за пятёрками! 🏆🍯",
    "🐦🙃 Чик... Утро добрым не бывает? Ещё как бывает, особенно когда видишь зелёные галочки ✅ в списке дедлайнов! Пора их добавить! 😉",
    "🐦🧭 Чик-чирик! Как ваш верный мёдоуказчик, показываю курс на сегодня: меньше паники, больше дела и побольше сладкого к чаю! 🍯🍩",
    "🐦🔥 ЧИРИК-ЧИК!! Разбудите своего внутреннего медоеда — ему вообще всё нипочём, и вам сегодня тоже будет всё по плечу! 🦡💪",
    "🐦🌈 Чик-чик~ Пусть сегодня попадётся лёгкий вопрос на семинаре, вкусный обед и ноль внезапных контрольных! 🍀🐝",
    "🐦📣 Внимание, улей! Чик! Объявляю сегодняшний день днём маленьких побед. Закройте хотя бы одну задачу — и вы уже молодцы! 🏅🍯",
    "🐦😴 Чик... Вижу, глаза ещё закрываются. Разрешаю потянуться как котик-пчёлка, но через 5 минут — в строй! 🐱🐝",
    "🐦💎 Чирик-чик! Вы уже прошли столько пар и докладов — неужели эта неделя вас остановит? Ни за что! Вперёд! ✨🔥",
    "🐦🍯 Чик-чик! Секрет продуктивного дня от мёдоуказчика: сделал дело — похвалил себя — съел вкусняшку. Не пропускайте ни один пункт! 😋",
    "🐦🌧️ Чик~ Какая бы погода ни была за окном, в нашей секретной пасеке всегда тепло и уютно. Берегите себя и не перегорайте! 💛🐝",
    "🐦🎯 Чики-чик! Выберите сегодня одну самую противную задачу и расправьтесь с ней первой — остаток дня покажется сказкой! ✨🍯",
    "🐦👑 Чик-чирик!! Доброе утро, элита историков! Пусть сегодня все источники находятся сами, а дедлайны тают как мёд в чае! 📜☕",
    "🐦💛 Чик-чик! Просто напоминаю: вы крутая команда, и вместе вы точно вытащите эту неделю на максимум! Полетели! 🚀🐝",
]


def load_last_messages() -> dict:
    if LAST_MESSAGES_FILE.exists():
        try:
            data = json.loads(LAST_MESSAGES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {"morning": list(data.get("morning", [])), "evening": list(data.get("evening", []))}
        except Exception:
            pass
    return {"morning": [], "evening": []}


def save_last_messages(state: dict):
    LAST_MESSAGES_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def delete_previous_messages(token: str, chat_id: str, msg_ids: list):
    for mid in msg_ids:
        url = f"https://api.telegram.org/bot{token}/deleteMessage"
        payload = {"chat_id": chat_id, "message_id": int(mid)}
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"deleteMessage {mid}:", resp.status)
        except Exception as e:
            print(f"deleteMessage {mid} skipped:", e)


def pick_random_image(folder: Path):
    if not folder.exists():
        return None
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTS]
    return random.choice(files) if files else None


def send_message(token: str, chat_id: str, topic_id: int, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "message_thread_id": topic_id, "text": text, "parse_mode": "HTML"}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return body.get("result", {}).get("message_id")


def send_photo(token: str, chat_id: str, topic_id: int, photo_path: Path, caption: str):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = f"----MedozakBoundary{uuid.uuid4().hex}"
    fields = {"chat_id": str(chat_id), "message_thread_id": str(topic_id), "caption": caption[:1024], "parse_mode": "HTML"}
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8"))
    mime_type = mimetypes.guess_type(photo_path.name)[0] or "image/jpeg"
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="{photo_path.name}"\r\nContent-Type: {mime_type}\r\n\r\n'.encode("utf-8")
        + photo_path.read_bytes()
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    req = urllib.request.Request(url, data=b"".join(parts), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("result", {}).get("message_id")


def normalize_tasks(item: dict) -> list:
    raw = item.get("tasks", [])
    item_done = bool(item.get("done", False))
    result = []
    for t in raw:
        if isinstance(t, dict):
            result.append({
                "text": str(t.get("text", "")).strip(),
                "assignee": str(t.get("assignee", "")).strip(),
                "done": bool(t.get("done", False)),
                "fileName": str(t.get("fileName", "")).strip(),
            })
        else:
            result.append({"text": str(t).strip(), "assignee": "", "done": item_done, "fileName": ""})
    return result


def is_overall_done(item: dict) -> bool:
    tasks = normalize_tasks(item)
    if tasks:
        return bool(item.get("done", False)) and all(t["done"] for t in tasks)
    return bool(item.get("done", False))


def format_task_line(task: dict) -> str:
    icon = "✅" if task["done"] else ("❌" if task["assignee"] else "⬜")
    who = task["assignee"] if task["assignee"] else "<i>Свободно</i>"
    file_tag = f" (📎 {task['fileName']})" if task["fileName"] else ""
    return f"  {icon} {who} — {task['text']}{file_tag}"


def format_evening_item(item: dict, target_date: str) -> str:
    subject = item["subject"]
    tasks = normalize_tasks(item)
    done = is_overall_done(item)
    done_parts = sum(1 for t in tasks if t["done"])
    template = random.choice(DONE_TEMPLATES if done else NOT_DONE_TEMPLATES)
    header = template.format(subject=subject)

    extra = ""
    if not done and tasks and done_parts == len(tasks):
        extra = " <i>(все части готовы — осталось подтвердить общую сдачу!)</i>"
    status_line = f"📌 <b>{subject}</b> ({target_date}) — <b>{'СДАН ✅' if done else 'НЕ СДАН ❌'}</b> [{done_parts}/{len(tasks)}]{extra}"
    task_lines = [format_task_line(t) for t in tasks] if tasks else ["  • (подробности не указаны)"]
    return "\n".join([header, "", status_line, *task_lines])


def run_evening(data: dict, token: str, chat_id: str, topic_id: int, dry_run: bool):
    target_date = os.environ.get("TEST_DATE", "").strip()
    if not target_date:
        target_date = (datetime.now(VL_TZ) + timedelta(days=1)).strftime("%d.%m")
    items = data.get(target_date, [])
    if not items:
        print(f"На {target_date} заданий нет.")
        return

    state = load_last_messages()
    if not dry_run and state["evening"]:
        delete_previous_messages(token, chat_id, state["evening"])

    new_ids = []
    for item in items:
        done = is_overall_done(item)
        text = format_evening_item(item, target_date)
        photo = pick_random_image(Path("images/done") if done else Path("images/not_done"))
        if dry_run:
            print("=== DRY RUN EVENING ===", "PHOTO:", photo)
            print(text)
            continue
        mid = send_photo(token, chat_id, topic_id, photo, text) if photo else send_message(token, chat_id, topic_id, text)
        if mid:
            new_ids.append(mid)

    if not dry_run:
        state["evening"] = new_ids
        save_last_messages(state)


def run_morning(data: dict, token: str, chat_id: str, topic_id: int, dry_run: bool):
    motivation = random.choice(MORNING_MOTIVATIONS)
    lines = [motivation, "", "📅 <b>Сводка дедлайнов и распределение задач:</b>"]
    total = 0
    done_count = 0

    for date_key, items in data.items():
        if not items:
            continue
        lines.append(f"\n🗓 <b>{date_key}</b>")
        for item in items:
            total += 1
            tasks = normalize_tasks(item)
            done_parts = sum(1 for t in tasks if t["done"])
            item_done = is_overall_done(item)
            if item_done:
                done_count += 1
            status_str = "<b>сдан ✅</b>" if item_done else f"<b>не сдан ❌</b> ({done_parts}/{len(tasks)})"
            lines.append(f"• <b>{item['subject']}</b> — {status_str}")
            for t in tasks:
                lines.append(format_task_line(t))

    if total == 0:
        lines.append("\nНа этой неделе дедлайнов пока нет — отдыхаем! 🍯")
    else:
        lines.append(f"\n📊 Закрыто общих дедлайнов: <b>{done_count} из {total}</b>")

    text = "\n".join(lines)
    if dry_run:
        print("=== DRY RUN MORNING ===")
        print(text)
        return

    state = load_last_messages()
    if state["morning"]:
        delete_previous_messages(token, chat_id, state["morning"])
    mid = send_message(token, chat_id, topic_id, text)
    state["morning"] = [mid] if mid else []
    save_last_messages(state)


def main():
    with open("schedule.json", encoding="utf-8") as f:
        data = json.load(f)
    dry_run = os.environ.get("DRY_RUN", "") == "1"
    mode = os.environ.get("BOT_MODE", "evening").strip().lower()
    token = os.environ.get("BOT_TOKEN", "")
    chat_id = os.environ.get("CHAT_ID", "")
    topic_id = int(os.environ.get("TOPIC_ID", "0") or 0)
    if mode == "morning":
        run_morning(data, token, chat_id, topic_id, dry_run)
    else:
        run_evening(data, token, chat_id, topic_id, dry_run)


if __name__ == "__main__":
    main()
