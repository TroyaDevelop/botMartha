from tokenize import group
from typing import Dict, Any
import vk_api
from vk_api.bot_longpoll import VkBotEventType
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import token, editable_stats, group_id
from messageController import get_last_name, get_random_joke, send_message, get_user_name, help_message, calculate_roll
from characterController import create_character, update_character_stat, show_character, load_characters, showInv, \
    updateInv, delInv
from states import set_user_state, get_user_state, clear_user_state, user_states
from utils import stat_map
from duelController import DuelController
from marriageController import marriage_controller

# Создание сессии VK
vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, group_id=group_id, wait=60)
vk = vk_session.get_api()
character_sheets = load_characters()
duels = {}

# Обработка событий от пользователей
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        # Получаем текст сообщения, peer_id и user_id
        message = event.obj.message
        text = message["text"].lower().strip()
        peer_id = message["peer_id"]
        user_id = message["from_id"]

        user_name = get_user_name(user_id)  # Получаем имя пользователя дальнейшего использования
        state = get_user_state(user_id)  # Получаем текущее состояние пользователя

        # Пошаговое создание персонажа
        if state == "awaiting_name":
            character_sheets[user_id] = {"name": text.title(), "level": 1}
            set_user_state(user_id, "awaiting_race")
            send_message(peer_id, "Какую расу выбрал ваш персонаж?")

        elif state == "awaiting_race":
            character_sheets[user_id]["race"] = text.capitalize()
            set_user_state(user_id, "awaiting_class")
            send_message(peer_id, "Какой класс у вашего персонажа?")

        elif state == "awaiting_class":
            # Завершаем создание персонажа
            character_sheets[user_id].update({
                "class": text.capitalize(),
                "hp": 10,
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10,
            })
            name = character_sheets[user_id]["name"]
            race = character_sheets[user_id]["race"]
            char_class = character_sheets[user_id]["class"]
            response = create_character(user_id, name, race, char_class)
            send_message(peer_id, response)
            character_sheets = load_characters()
            clear_user_state(user_id)

        elif state == "choosing_stat":
            if text in ["сила", "ловкость", "интеллект", "мудрость", "харизма", "телосложение"]:
                stat = stat_map[text]
                user_states[user_id] = f"awaiting_{stat}_value"
                send_message(peer_id, f"Введите новое значение для характеристики '{text}'.")
            else:
                send_message(peer_id, "Недопустимая характеристика. Пожалуйста, выберите одну из предложенных.")
        elif user_id in user_states and any(
                user_states[user_id] == f"awaiting_{stat}_value" for stat in editable_stats):
            # Проверка существования персонажа перед обновлением значения
            if str(user_id) not in character_sheets:
                send_message(peer_id, "У вас нет созданного персонажа. Сначала создайте его.")
                del user_states[user_id]  # Очищаем состояние, если персонажа нет
            else:
                # Определяем, какую характеристику обновляем
                stat = [s for s in editable_stats if user_states[user_id] == f"awaiting_{s}_value"][0]
                response = update_character_stat(user_id, stat, text)
                send_message(peer_id, response)
                # Убираем пользователя из user_states после обработки
                del user_states[user_id]  # Сбрасываем состояние, чтобы избежать бесконечного цикла

        elif state == "awaiting_inventory_item":
            parts = text.split(",", maxsplit=1)  # Разделяем строку на две части через запятую
            if len(parts) < 2:
                send_message(peer_id,
                             "Пожалуйста, укажите название предмета и его количество через запятую (например: 'меч, 2').")
            else:
                item_name = parts[0].strip()  # Убираем лишние пробелы вокруг названия
                try:
                    quantity = int(parts[1].strip())  # Преобразуем вторую часть в число
                    if quantity <= 0:
                        send_message(peer_id, "Количество должно быть положительным числом.")
                    else:
                        response = updateInv(user_id, item_name, quantity)
                        send_message(peer_id, response)
                except ValueError:
                    send_message(peer_id, "Количество должно быть числом. Попробуйте снова.")
            clear_user_state(user_id)  # Очищаем состояние после обработки ввода

        elif state == "awaiting_inventory_removal":
            parts = text.split(",", maxsplit=1)  # Разделяем строку на две части через запятую
            if len(parts) < 2:
                send_message(peer_id,
                             "Пожалуйста, укажите название предмета и его количество для удаления через запятую (например: 'зелье лечения, 1').")
            else:
                item_name = parts[0].strip()  # Убираем лишние пробелы вокруг названия
                try:
                    quantity = int(parts[1].strip())  # Преобразуем вторую часть в число
                    if quantity <= 0:
                        send_message(peer_id, "Количество должно быть положительным числом.")
                    else:
                        response = delInv(user_id, item_name, quantity)
                        send_message(peer_id, response)
                except ValueError:
                    send_message(peer_id, "Количество должно быть числом. Попробуйте снова.")

            clear_user_state(user_id)  # Очищаем состояние после обработки ввода

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

        # elif text == "инв":
        #     inv = showInv(user_id)
        #     send_message(peer_id, inv)

        # elif text == "инв доб":
        #     if str(user_id) not in character_sheets:
        #         send_message(peer_id, "Сначала создайте персонажа.")
        #     else:
        #         set_user_state(user_id, "awaiting_inventory_item")
        #         send_message(peer_id, "Введите название предмета и его количество (например: 'меч, 2').")

        # elif text == "инв удал":
        #     if str(user_id) not in character_sheets:
        #         send_message(peer_id, "Сначала создайте персонажа.")
        #     else:
        #         set_user_state(user_id, "awaiting_inventory_removal")
        #         send_message(peer_id,
        #                      "Введите название предмета и его количество для удаления через запятую (например: 'зелье лечения, 1').")

        # elif text == "хочу стать авантюристом":
        #     if str(user_id) in character_sheets:
        #         send_message(peer_id, "Вы уже состоите в гильдии авантюристов!")
        #     else:
        #         set_user_state(user_id, "awaiting_name")
        #         send_message(peer_id, "Отлично! Как вас зовут?")

        # elif text == "изменить характеристику":
        #     character = character_sheets.get(str(user_id))
        #     if not character:
        #         send_message(peer_id, "К сожалению, вы не состоите в гильдии авантюристов.")
        #     else:
        #         set_user_state(user_id, "choosing_stat")
        #         send_message(peer_id, "Какую характеристику вы хотите изменить? (сила, ловкость, интеллект, мудрость, харизма, телосложение)")

        # elif text == "покажи мою лицензию":
        #     response = show_character(user_id)
        #     send_message(peer_id, response)

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
                    user1 = get_user_name(id1) + " " + get_last_name(id1)
                    user2 = get_user_name(id2) + " " + get_last_name(id2)
                    response += f'{user1} + {user2} (с {data["date"]})\n'
            send_message(peer_id, response)

        else:
            #Условие если команда не найдена.
            pass
