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

def send_message(peer_id: int, message: str) -> None:
    attempts = 0
    while attempts < MAX_RETRIES:
        try:
            vk.messages.send(
                peer_id=peer_id,
                message=message,
                random_id=random.randint(1, 10**6)
            )
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
        return f"[id{user_id}|{nickname}]"
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        first_name = user_info[0].get('first_name', '')
        last_name = user_info[0].get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        return f"[id{user_id}|{full_name}]"
    return "друг"

help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с командами:\n\n"
    "Дуэль -  вызывает другого игрока на дуэль.\n"
    "Анекдот -  вызывает анекдот.\n"
    "Брак -  предлагает заключить брак с другим пользователем.\n"
    "Для помощи с бросками кубиков напиши '/помощь'.\n"
)

def get_random_joke():
    with open('data/jokes.json', 'r', encoding='utf-8') as file:
        jokes = json.load(file)
    return random.choice(jokes)