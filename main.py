from tokenize import group
from typing import Dict, Any
import vk_api
from vk_api.bot_longpoll import VkBotEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import token, group_id
from controllers.messageController import get_random_joke, send_message, get_user_name, help_message, calculate_roll
from controllers.duelController import DuelController
from controllers.marriageController import MarriageController
from controllers.profileController import ProfileController

# Создание сессии VK
vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id=group_id, wait=60)
vk = vk_session.get_api()
duels = {}
marriage_controller = MarriageController()
profile_controller = ProfileController()

# Обработка событий от пользователей
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        # Получаем текст сообщения, peer_id и user_id
        message = event.obj.message
        text = message["text"].lower().strip()
        peer_id = message["peer_id"]
        user_id = message["from_id"]

        user_name = get_user_name(user_id)  # Получаем имя пользователя дальнейшего использования

        if "марта" in text:
            roll_command = text.split("марта", 1)[1].strip()  # Убираем лишние пробелы
            result = calculate_roll(user_name, roll_command)
            send_message(peer_id, result)
        elif "/" in text:
            roll_command = text.split("/", 1)[1].strip()  # Убираем лишние пробелы
            result = calculate_roll(user_name, roll_command)
            send_message(peer_id, result)

        # Обработка команд от пользователя, если он не в процессе создания персонажа
        elif text == "привет":
            send_message(peer_id, f"Здравствуйте, {user_name}! Чем могу помочь?")

        elif text == "пока":
            send_message(peer_id, f"Удачи вам, {user_name}!")

        elif text == "помощь":
            send_message(peer_id, help_message)

        elif text == "анекдот":
            send_message(peer_id, get_random_joke())

        elif text == "дуэль":
            if message.get('reply_message'):
                response = DuelController.handle_duel_command(user_id, message['reply_message'])
            else:
                response = DuelController.handle_duel_command(user_id)
            send_message(peer_id, response)

        elif text == "принять дуэль":
            response = DuelController.handle_accept_duel(user_id)
            send_message(peer_id, response)

        elif text == "выстрел":
            response = DuelController.handle_shoot_command(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "дуэль стат":
            stats = DuelController.get_stats(peer_id)
            if not stats:
                response = 'Статистика дуэлей пока пуста.'
            else:
                response = 'Статистика побед в дуэлях:\n'
                for user_id, wins in stats.items():
                    user_name = get_user_name(user_id)
                    rank = DuelController.get_rank(wins)
                    response += f'{user_name}: {wins} ({rank})\n'
            send_message(peer_id, response)

        elif text == "брак":
            if message.get('reply_message'):
                response = marriage_controller.propose_marriage(user_id, peer_id, message['reply_message'])
            else:
                response = marriage_controller.propose_marriage(user_id, peer_id)
            send_message(peer_id, response)

        elif text == "принять брак":
            response = marriage_controller.accept_marriage(user_id)
            send_message(peer_id, response)

        elif text == "развод":
            response = marriage_controller.divorce(user_id, peer_id)
            send_message(peer_id, response)

        elif text == "подтвердить развод":
            response = marriage_controller.confirm_divorce(user_id)
            send_message(peer_id, response)

        elif text == "браки":
            marriages = marriage_controller.get_marriages(peer_id)
            if not marriages:
                response = 'В нашей гильдии пока никто не в браке!'
            else:
                response = 'Список браков:\n'
                for pair, data in marriages.items():
                    id1, id2 = eval(pair)
                    user1 = get_user_name(id1)
                    user2 = get_user_name(id2)
                    response += f'{user1} + {user2} (с {data["date"]})\n'
            send_message(peer_id, response)

        elif text.startswith("мне ник"):
            nickname = text.split("мне ник", 1)[1].strip()
            if nickname:
                nickname = nickname[0].upper() + nickname[1:]
                profile_controller.set_nickname(user_id, nickname)
                send_message(peer_id, f"Ваш никнейм изменен на '{nickname}'.")
            else:
                send_message(peer_id, "Пожалуйста, укажите никнейм после команды 'мне ник'.")

        else:
            #Условие если команда не найдена.
            pass
