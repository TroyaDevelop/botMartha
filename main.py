from tokenize import group
from typing import Dict, Any
import vk_api
from vk_api.bot_longpoll import VkBotEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import token, group_id
from controllers.diceController import calculate_roll
from controllers.messageController import burn_command, choose_option, get_random_joke, hug_command, kiss_command, bonk_command, slap_command, send_message, get_user_name, help_message
from controllers.duelController import DuelController
from controllers.marriageController import MarriageController
from controllers.profileController import ProfileController
from controllers.rouletteController import RouletteController
from controllers.characterController import CharacterController
from controllers.lottoController import LottoController

# Создание сессии VK
vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id=group_id, wait=60)
vk = vk_session.get_api()
duels = {}
marriage_controller = MarriageController()
profile_controller = ProfileController()
roulette_controller = RouletteController()
character_controller = CharacterController()
lotto_controller = LottoController()

# Обработка событий от пользователей
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        # Получаем текст сообщения, peer_id и user_id
        message = event.obj.message
        text = message["text"].lower().strip()
        peer_id = message["peer_id"]
        user_id = message["from_id"]

        user_name = get_user_name(user_id)  # Получаем имя пользователя дальнейшего использования

        # Проверяем команду выбора "или" перед другими командами
        if " или " in text:
            response = choose_option(text)
            if response:
                send_message(peer_id, response)
                continue  # Переходим к следующему сообщению

        if "марта" in text:
            roll_command = text.split("марта", 1)[1].strip()  # Убираем лишние пробелы
            result = calculate_roll(user_name, roll_command)
            send_message(peer_id, result)
        elif "/" in text:
            roll_command = text.split("/", 1)[1].strip()  # Убираем лишние пробелы
            result = calculate_roll(user_name, roll_command)
            send_message(peer_id, result)

        # Проверяем, находится ли пользователь в процессе создания персонажа
        if character_controller.is_in_character_creation(user_id):
            # Проверяем, не хочет ли пользователь отменить создание персонажа
            if text == "отмена" or text == "отменить":
                response = character_controller.reset_character_creation(user_id)
                send_message(peer_id, response)
                continue
            
            # Обрабатываем ответ пользователя в процессе создания персонажа
            response = character_controller.process_character_creation(user_id, message["text"])
            if response:
                send_message(peer_id, response)
            continue
        
        # Обработка команд от пользователя, если он не в процессе создания персонажа
        if text == "привет":
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

        elif text == "дуэль стата":
            stats = DuelController.get_stats(peer_id)
            if not stats:
                response = 'Статистика дуэлей пока пуста.'
            else:
                response = 'Статистика побед в дуэлях:\n'
                for user_id, user_stats in stats.items():
                    user_name = get_user_name(user_id)
                    wins = user_stats["wins"]
                    streak = user_stats["streak"]
                    rank = DuelController.get_rank(wins)
                    streak_info = f" | Серия: {streak}🔥" if streak >= 1 else ""
                    response += f'{user_name}: {wins} ({rank}){streak_info}\n'
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

        # elif text == "мой профиль":
        #     response = profile_controller.get_profile(user_id)
        #     send_message(peer_id, response)

        elif text.startswith("мне ник"):
            nickname = text.split("мне ник", 1)[1].strip()
            if nickname:
                nickname = nickname[0].upper() + nickname[1:]
                profile_controller.set_nickname(user_id, nickname)
                send_message(peer_id, f"Ваш никнейм изменен на '{nickname}'.")
            else:
                send_message(peer_id, "Пожалуйста, укажите никнейм после команды 'мне ник'.")

        elif text.startswith("обнять"):
            reply_message = event.message.get('reply_message')
            response = hug_command(user_id, reply_message)
            send_message(peer_id, response)

        elif text.startswith("поцеловать"):
            reply_message = event.message.get('reply_message')
            response = kiss_command(user_id, reply_message)
            send_message(peer_id, response)

        elif text.startswith("сжечь"):
            reply_message = event.message.get('reply_message')
            response, image_url = burn_command(user_id, reply_message)
            send_message(peer_id, response, image_url)

        elif text.startswith("шлёпнуть") or text.startswith("шлепнуть"):
            reply_message = event.message.get('reply_message')
            response = slap_command(user_id, reply_message)
            send_message(peer_id, response)

        elif text.startswith("боньк"):
            reply_message = event.message.get('reply_message')
            response = bonk_command(user_id, reply_message)
            send_message(peer_id, response)

        elif text == "рулетка":
            response = roulette_controller.start_game(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "рулетка вступить":
            response = roulette_controller.join_game(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "рулетка начать":
            response = roulette_controller.start_roulette(peer_id)
            send_message(peer_id, response)

        elif text == "щелчок":
            response = roulette_controller.shoot(peer_id, user_id)
            send_message(peer_id, response)
            
        # Команды для игры в лото
        elif text == "лото":
            response = lotto_controller.start_game(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "лото вступить":
            response = lotto_controller.join_game(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "лото начать":
            response = lotto_controller.start_lotto(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "лото число":
            response = lotto_controller.draw_number(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "лото карточка":
            response = lotto_controller.check_card(peer_id, user_id)
            send_message(peer_id, response)

        elif text == "лото числа":
            response = lotto_controller.get_drawn_numbers(peer_id)
            send_message(peer_id, response)

        elif text == "лото стоп":
            response = lotto_controller.end_game(peer_id, user_id)
            send_message(peer_id, response)
            
        # Команды для работы с персонажами D&D 5e
        elif text == "получить лицензию" or text == "новый персонаж":
            response = character_controller.start_character_creation(user_id, peer_id)
            send_message(peer_id, response)

        elif text == "лицензия" or text == "лист персонажа":
            response = character_controller.get_character_sheet(user_id, peer_id)
            send_message(peer_id, response)

        elif text == "сдать лицензию":
            response = character_controller.delete_character(user_id, peer_id)
            send_message(peer_id, response)

        else:
            #Условие если команда не найдена.
            pass
