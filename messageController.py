# messages.py
import random
import re
import vk_api
from config import token

# Ограничения на количество кубиков и граней
MAX_DICE_COUNT = 100
MAX_DICE_SIDES = 100

# Эмодзи для критических бросков 20-гранных кубиков и модификатора
CRIT_FAIL_EMOJI = "😱"
CRIT_SUCCESS_EMOJI = "🎉"
GEAR_EMOJI = "⚙️"

# Инициализация сессии и API ВКонтакте
vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()


def send_message(peer_id: int, message: str) -> None:
    vk.messages.send(
        peer_id=peer_id,
        message=message,
        random_id=random.randint(1, 10**6)
    )


def get_user_name(user_id: int) -> str:
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        return user_info[0].get('first_name', "друг")
    return "друг"


def roll_dice(sides: int, rolls: int = 1) -> list[int]:
    return [random.randint(1, sides) for _ in range(rolls)]


def is_fox(username: str) -> str:
    return "Лисичка" if username == "Moonlight" else username


help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с системой бросков кубиков:\n\n"
    "🎲 Основные команды для бросков кубиков:\n"
    "- /д20 — бросить один 20-гранный кубик.\n"
    "- /3д6 — бросить три 6-гранных кубика и показать сумму.\n"
    "- /д20+5 — бросить один 20-гранный кубик и добавить модификатор +5.\n\n"
    "📋 Примеры команд:\n"
    "- /д20 — обычный бросок 20-гранного кубика.\n"
    "- /2д10+3 — бросить два 10-гранных кубика и добавить модификатор +3.\n\n"
    "Напиши 'помощь', если тебе снова понадобится эта инструкция. Удачи в бросках! 🎲"
)


def calculate_roll(username: str, command: str) -> str:
    # Нормализуем команду: заменяем альтернативные символы на стандартный "д"
    normalized_command = command.replace("к", "д").replace("d", "д")
    lines = normalized_command.splitlines()
    results = []
    display_name = is_fox(username)

    if not lines:
        return f"Да, {display_name}?"

    # Регулярное выражение для парсинга команды броска кубиков.
    dice_pattern = re.compile(
        r'^(?P<count>\d*)д(?P<sides>\d+)((?P<modifiers>([+-]\d+)+))?$'
    )
    modifier_pattern = re.compile(r'([+-]\d+)')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Удаляем ведущий слеш, если он присутствует
        line_clean = line.lstrip('/')
        match = dice_pattern.fullmatch(line_clean)
        if not match:
            results.append(f"Некорректная команда, {display_name}. Пример: /д20+5.")
            continue

        # Определяем количество кубиков (если не указано, то 1)
        count_str = match.group('count')
        dice_count = int(count_str) if count_str.isdigit() else 1

        # Количество граней кубика
        dice_sides = int(match.group('sides'))

        # Обрабатываем модификаторы (например, +5 или -1)
        modifiers_str = match.group('modifiers') or ""
        modifier_values = modifier_pattern.findall(modifiers_str)

        # Суммируем все модификаторы (положительные и отрицательные)
        total_modifiers = sum(int(mod) for mod in modifier_values)

        # Суммируем одинаковые модификаторы (например, два `-4` должны быть `-8`)
        simplified_modifiers = {}
        for mod in modifier_values:
            if mod in simplified_modifiers:
                simplified_modifiers[mod] += 1
            else:
                simplified_modifiers[mod] = 1

        # Формируем строку для модификаторов
        modifier_display = ""
        for mod, count in simplified_modifiers.items():
            if mod.startswith("+"):
                modifier_display += f" + {int(mod[1:]) * count} {GEAR_EMOJI}"
            elif mod.startswith("-"):
                modifier_display += f" - {int(mod[1:]) * count} {GEAR_EMOJI}"

        if dice_count > MAX_DICE_COUNT or dice_sides > MAX_DICE_SIDES or dice_sides <= 0:
            results.append(f"Слишком много кубиков или граней, {display_name}.")
            continue

        roll_results = roll_dice(dice_sides, dice_count)
        total = sum(roll_results) + total_modifiers

        # Если сумма результата и модификаторов <= 0, выводим "Выпала 1"
        if total <= 0:
            results.append(f"{display_name}, выпала 1. ({modifier_display})")
            continue

        # Специальная обработка для 20-гранного кубика
        if dice_sides == 20:
            if dice_count == 1:
                roll = roll_results[0]
                if roll == 1:
                    roll_detail = f"Критический провал {CRIT_FAIL_EMOJI}"
                elif roll == 20:
                    roll_detail = f"Критический успех {CRIT_SUCCESS_EMOJI}"
                else:
                    roll_detail = str(roll)
            else:
                detailed_rolls = []
                for roll in roll_results:
                    if roll == 1:
                        detailed_rolls.append(f"{roll}{CRIT_FAIL_EMOJI}")
                    elif roll == 20:
                        detailed_rolls.append(f"{roll}{CRIT_SUCCESS_EMOJI}")
                    else:
                        detailed_rolls.append(str(roll))
                roll_detail = " + ".join(detailed_rolls)
        else:
            roll_detail = " + ".join(map(str, roll_results))

        results.append(f"{display_name}, Итог: {total}. ({roll_detail}{modifier_display})")

    return "\n".join(results)
