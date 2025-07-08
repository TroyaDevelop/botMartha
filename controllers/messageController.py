import random
import vk_api
from vk_api import VkUpload
from config import token
import time
import json
from controllers.profileController import ProfileController

profile_controller = ProfileController()

# Инициализация сессии и API ВКонтакте
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
upload = VkUpload(vk)  # единый объект загрузчика

MAX_RETRIES = 10  # Количество попыток переподключения
RETRY_DELAY = 15  # Задержка перед повторной попыткой в секундах


def _upload_photo(path: str) -> str:
    photo = upload.photo_messages(path)[0]
    return f"photo{photo['owner_id']}_{photo['id']}"


def _upload_doc(path: str, peer_id: int, doc_type: str | None = None) -> str:
    """Загружает документ (включая GIF) и формирует attachment.

    `VkUpload.document_message` в разных версиях vk_api возвращает либо список с
    одним элементом, либо словарь вида `{"doc": {..}}`. Берём оба случая.
    """

    if doc_type:
        raw = upload.document_message(path, peer_id=peer_id, doc_type=doc_type)
    else:
        raw = upload.document_message(path, peer_id=peer_id)

    # --- Унифицируем к словарю с полями owner_id / id ---
    if isinstance(raw, list):
        doc_dict = raw[0]
    elif isinstance(raw, dict):
        doc_dict = raw.get("doc", raw)  # если внутри ключ 'doc'
    else:
        raise RuntimeError("Неожиданный формат ответа VK API при загрузке документа")

    owner_id = doc_dict["owner_id"]
    doc_id   = doc_dict["id"]
    return f"doc{owner_id}_{doc_id}"


def send_message(
    peer_id: int,
    message: str,
    *,
    image_path: str | None = None,
    gif_path: str | None = None,
    doc_path: str | None = None,
) -> None:
    """Отправляет сообщение. Один из *path аргументов может быть задан.*

    - image_path → вкладываем как photo (jpeg/png)
    - gif_path   → **документ** типа GIF
    - doc_path   → любой doc (txt/pdf/zip) или gif, если gif_path не использован
    """

    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            attachment: str | None = None

            if image_path:
                attachment = _upload_photo(image_path)
            elif gif_path:
                attachment = _upload_doc(gif_path, peer_id, doc_type="gif")
            elif doc_path:
                attachment = _upload_doc(doc_path, peer_id)

            vk.messages.send(
                peer_id=peer_id,
                message=message,
                attachment=attachment,
                random_id=0,
            )
            break
        except vk_api.VkApiError as e:
            attempts += 1
            if attempts < MAX_RETRIES:
                print(f"Ошибка отправки: {e}. Повтор через {RETRY_DELAY} с.")
                time.sleep(RETRY_DELAY)
            else:
                print("Не удалось отправить сообщение.")


def get_user_name(user_id: int) -> str:
    nickname = profile_controller.get_nickname(user_id)
    if nickname:
        return nickname

    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        first_name = user_info[0].get("first_name", "")
        last_name = user_info[0].get("last_name", "")
        return f"{first_name} {last_name}".strip()
    return "друг"

# -------- «или»-выбор --------

def choose_option(text: str) -> str | None:
    lower = text.lower().strip()
    if " или " in lower and lower.startswith("марта"):
        options = [opt.strip() for opt in lower[5:].split(" или ") if opt.strip()]
        if len(options) >= 2:
            return random.choice(options)
    return None

# -------- Справка и анекдоты --------
help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с командами:\n\n"
    "Дуэль — вызывает другого игрока на дуэль.\n"
    "Анекдот — присылает случайный анекдот.\n"
    "Брак — предлагает заключить брак с другим пользователем.\n"
    "Для справки по кубам напиши '/помощь'.\n\n"
    "РУССКАЯ РУЛЕТКА\n"
    "Рулетка — начать набор игроков.\n"
    "Рулетка вступить — присоединиться.\n"
    "Рулетка начать — запустить игру.\n"
)


def get_random_joke() -> str:
    with open("data/jokes.json", "r", encoding="utf-8") as f:
        jokes = json.load(f)
    return random.choice(jokes)

# -------- Эмоциональные реакции --------

def _reaction_template(action_verb: str, emoji: str, user_id: int, reply_message) -> str:
    if reply_message:
        target_id = reply_message["from_id"]
        return f"{get_user_name(user_id)} {action_verb} {get_user_name(target_id)} {emoji}"
    return f"{get_user_name(user_id)} {action_verb} себя {emoji}"


def hug_command(user_id, reply_message):
    return _reaction_template("обнимает", "🤗", user_id, reply_message)


def kiss_command(user_id, reply_message):
    return _reaction_template("целует", "🥰", user_id, reply_message)


def bonk_command(user_id, reply_message):
    return _reaction_template("бонькает", "🔨", user_id, reply_message)


def slap_command(user_id, reply_message):
    return _reaction_template("шлёпает", "😏", user_id, reply_message)

# -------- Сжечь --------

def burn_command(user_id, reply_message):
    burn_images = [
        "img/burn1.jpg",
        "img/burn2.jpg",
        "img/burn3.jpg",
    ]
    msg = _reaction_template("сжигает", "🔥", user_id, reply_message)
    return msg, random.choice(burn_images)

# -------- Сожрать (GIF как документ) --------

def devour_command(user_id, reply_message):
    devour_docs = [
        "gif/DreadybearTrueJumpscare.gif",
    ]
    msg = _reaction_template("сжирает", "😈", user_id, reply_message)
    return msg, random.choice(devour_docs)
