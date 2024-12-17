# messages.py
import vk_api
from config import token
import random
import re

vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()


def send_message(peer_id, message):
    vk.messages.send(peer_id=peer_id, message=message, random_id=0)


def get_user_name(user_id):
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        return user_info[0].get('first_name', "друг")
    return "друг"


def roll_dice(sides, rolls=1):
    results = [random.randint(1, sides) for _ in range(rolls)]
    return results


help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с системой бросков кубиков:\n\n"
    "🎲 **Основные команды для бросков кубиков:**\n"
    "- `/д20` — бросить один 20-гранный кубик.\n"
    "- `/3д6` — бросить три 6-гранных кубика и показать сумму.\n"
    "- `/д20+5` — бросить один 20-гранный кубик и добавить модификатор +5.\n"
    "📋 **Примеры команд:**\n"
    "- `/д20` — обычный бросок 20-гранного кубика.\n"
    "- `/2д10+3` — бросить два 10-гранных кубика и добавить модификатор +3.\n"
    "Напиши `/помощь`, если тебе снова понадобится эта инструкция. Удачи в бросках! 🎲")


def calculate_roll(command: str) -> str:
    """
    Обрабатывает команды броска кубиков.
    :param command: Команда(ы) в формате "к20", "2к6+3", можно передать несколько команд через перенос строки.
    :return: Результат бросков в текстовом формате.
    """
    # Заменяем все "к" на "д" для правильной обработки
    command = command.replace("к", "д").replace("d", "д")

    # Разделяем команды по строкам
    commands = command.splitlines()

    message = ""

    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue

        # Разделяем команду на отдельные элементы (например, "2д6+3")
        split_index = cmd.find("д")
        if split_index == -1:
            message += f"Некорректная команда: {cmd}. Убедитесь в правильности формата, например: /д20+5.\n"
            continue

        # Извлекаем количество кубиков и граней
        dice_count_str = cmd[:split_index].strip()
        rest = cmd[split_index + 1:].strip()

        # Определяем количество кубиков (по умолчанию 1)
        dice_count = int(dice_count_str) if dice_count_str.isdigit() else 1

        if dice_count > 100:
            message += f"Слишком большое количество кубиков, господин."
            continue

        # Разделяем оставшуюся часть команды на грани и модификаторы
        dice_sides_str = ""
        modifiers = []
        modifier_steps = []
        current_value = ""
        current_sign = "+"

        for char in rest:
            if char.isdigit():
                current_value += char
            elif char in "+-":
                if current_value:
                    if dice_sides_str == "":
                        dice_sides_str = current_value
                    else:
                        value = int(current_value) if current_sign == "+" else -int(current_value)
                        modifiers.append(value)
                        modifier_steps.append(f"{current_sign}{current_value}")
                    current_value = ""
                current_sign = char

        if current_value:
            if dice_sides_str == "":
                dice_sides_str = current_value
            else:
                value = int(current_value) if current_sign == "+" else -int(current_value)
                modifiers.append(value)
                modifier_steps.append(f"{current_sign}{current_value}")

        # Проверяем корректность количества граней
        if not dice_sides_str.isdigit():
            message += f"Некорректное количество граней в команде: {cmd}.\n"
            continue

        dice_sides = int(dice_sides_str)

        if dice_sides > 10000:
            message += "Слишком большое количество граней, господин."
            continue

        # Проверяем положительность значений
        if dice_count <= 0 or dice_sides <= 0:
            message += f"Количество кубиков и граней должно быть положительным числом в команде: {cmd}.\n"
            continue

        # Выполняем бросок кубиков
        rolls = roll_dice(dice_sides, dice_count)
        rolls_str = ", ".join(map(str, rolls))

        # Рассчитываем итоговый модификатор
        modifier_value = sum(modifiers)

        # Формируем сообщение о результатах
        if dice_count == 1 and dice_sides == 20:
            crit = "Критический успех!" if rolls[0] == 20 else "Критический провал!" if rolls[0] == 1 else ""
            message += f"Результат броска: {rolls[0]}. {crit}\n"
        elif dice_count >= 2:
            message += f"Результаты бросков: {rolls_str}.\n"
        else:
            message += f"Результат броска: {rolls[0]}\n"

        total = sum(rolls) + modifier_value
        modifier_expression = " ".join(modifier_steps)
        message += f" Итог: {sum(rolls)} {modifier_expression} = {total}.\n"

    return message


