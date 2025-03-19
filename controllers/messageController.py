import random
import vk_api
from config import token
import time
import json
from controllers.profileController import ProfileController
profile_controller = ProfileController()

# Инициализация сессии и API ВКонтакте
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()

MAX_RETRIES = 10  # Количество попыток переподключения
RETRY_DELAY = 15  # Задержка перед повторной попыткой в секундах

def send_message(peer_id: int, message: str, image_url=None, gif_url=None) -> None:
    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            if image_url:
                upload = vk_api.VkUpload(vk)
                photo = upload.photo_messages(image_url)[0]
                attachment = f"photo{photo['owner_id']}_{photo['id']}"
                vk.messages.send(peer_id=peer_id, message=message, attachment=attachment, random_id=0)
            else:     
                vk.messages.send(peer_id=peer_id, message=message, random_id=0)
            break  # Если сообщение отправлено, выходим из цикла
        except vk_api.VkApiError as e:
            attempts += 1
            if attempts < MAX_RETRIES:
                print(f"Ошибка при отправке сообщения: {e}. Повторная попытка через {RETRY_DELAY} секунд.")
                time.sleep(RETRY_DELAY)  # Ждем перед повторной попыткой
            else:
                print("Не удалось отправить сообщение после нескольких попыток.")

def get_user_name(user_id: int) -> str:
    nickname = profile_controller.get_nickname(user_id)
    if nickname:
        return f"{nickname}"
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        first_name = user_info[0].get('first_name', '')
        last_name = user_info[0].get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        return f"{full_name}"
    return "друг"

def choose_option(text):
    if " или " in text:
        options = text.split(" или ")
        if len(options) >= 2:
            return random.choice(options)
    return None

help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с командами:\n\n"
    "Дуэль -  вызывает другого игрока на дуэль.\n"
    "Анекдот -  вызывает анекдот.\n"
    "Брак -  предлагает заключить брак с другим пользователем.\n"
    "Для помощи с бросками кубиков напиши '/помощь'.\n"
    
    "РУССКАЯ РУЛЕТКА\n"
    "Рулетка - начинает игру в русскую рулетку.\n"
    "Рулетка присоединиться - присоединяет к игре в русскую рулетку.\n"
    "Рулетка начать - запускает игру в русскую рулетку.\n"
    "Рулетка выстрел - делает выстрел в русской рулетке.\n"
)

def get_random_joke():
    with open('data/jokes.json', 'r', encoding='utf-8') as file:
        jokes = json.load(file)
    return random.choice(jokes)

def hug_command(user_id, reply_message):
    if reply_message:
        target_id = reply_message['from_id']
        user_name = get_user_name(user_id)
        target_name = get_user_name(target_id)
        return f"{user_name} обнимает {target_name} 🤗"
    else:
        return f"Сам себя не обнимешь..."

def kiss_command(user_id, reply_message):
    if reply_message:
        target_id = reply_message['from_id']
        user_name = get_user_name(user_id)
        target_name = get_user_name(target_id)
        return f"{user_name} целует {target_name} 🥰"
    else:
        return f"Сам себя не поцелуешь..."

def burn_command(user_id, reply_message):
    burn_images = [
        "img/burn1.jpg",
        "img/burn2.jpg",
        "img/burn3.jpg"
    ]
    if reply_message:
        target_id = reply_message['from_id']
        user_name = get_user_name(user_id)
        target_name = get_user_name(target_id)
        return f"{user_name} сжигает {target_name} 🔥", random.choice(burn_images)
    else:
        return f"{get_user_name(user_id)} сжигает себя 🔥", random.choice(burn_images)

def bonk_command(user_id, reply_message):
    if reply_message:
        target_id = reply_message['from_id']
        user_name = get_user_name(user_id)
        target_name = get_user_name(target_id)
        return f"{user_name} бонькает {target_name}🔨"
    else:
        return f"{get_user_name(user_id)} бонькает себя🔨"

def slap_command(user_id, reply_message):
    if reply_message:
        target_id = reply_message['from_id']
        user_name = get_user_name(user_id)
        target_name = get_user_name(target_id)
        return f"{user_name} шлёпает {target_name} 😏"
    else:
        return f"{get_user_name(user_id)} шлёпает себя 😏"
