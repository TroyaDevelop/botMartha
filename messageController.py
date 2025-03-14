import random
import re
import vk_api
from config import token
import time
import json

# Ограничения на количество кубиков и граней
MAX_DICE_COUNT = 250
MAX_DICE_SIDES = 100

# Эмодзи для критических бросков 20-гранных кубиков и модификатора
CRIT_FAIL_EMOJI = "☠️"
CRIT_SUCCESS_EMOJI = "💥"
GEAR_EMOJI = "⚙️"

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
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        return user_info[0].get('first_name', "друг")
    return "друг"

def get_last_name(user_id: int) -> str:
    user_info = vk.users.get(user_ids=user_id)
    if user_info:
        return user_info[0].get('last_name', "батькович")
    return "батькович"
    
def biased_roll(sides: int, exponent: float = 0.8) -> int:
    """
    Функция смещенного броска кубика.
    При exponent < 1 увеличивается шанс выпадения высоких значений.
    Изменена формула, чтобы при максимально возможном значении r выпадает sides.
    """
    r = random.random()  # равномерное число от 0 до 1
    return int(sides * (r ** exponent)) + 1

def roll_dice(sides: int, rolls: int = 1) -> list[int]:
    """
    Использует biased_roll вместо random.randint для смещения вероятности к большим числам.
    """
    return [biased_roll(sides) for _ in range(rolls)]

def is_fox(username: str) -> str:
    return "Лисичка" if username == "Moonlight" else username

help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с командами:\n\n"
    "Дуэль -  вызывает другого игрока на дуэль.\n"
    "Анекдот -  вызывает анекдот.\n"
    "Брак -  предлагает заключить брак с другим пользователем.\n"
    "Для помощи с бросками кубиков напиши '/помощь'.\n"
)

dice_help_message = (
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

def get_random_joke():
    with open('jokes.json', 'r', encoding='utf-8') as file:
        jokes = json.load(file)
    return random.choice(jokes)

def calculate_roll(username: str, command: str) -> str:
    # Нормализуем команду: заменяем альтернативные символы на стандартный "д"
    normalized_command = command.replace("к", "д").replace("d", "д")
    lines = normalized_command.splitlines()
    results = []
    display_name = is_fox(username)

    if not lines:
        return f"Да, {display_name}?"

    # Если команда /помощь, возвращаем инструкцию
    if '/помощь' in normalized_command.lower() or 'помощь' in normalized_command.lower():
        return dice_help_message
    elif 'поцелуй' in normalized_command.lower():
        return f"😘"

    # Регулярное выражение для парсинга команды броска кубиков.
    dice_pattern = re.compile(r'(?P<count>\d*)д(?P<sides>\d+)((?P<modifiers>([+-]\d+)+))?')
    modifier_pattern = re.compile(r'([+-]\d+)')

    # Ищем все команды бросков кубиков в тексте
    matches = dice_pattern.finditer(normalized_command)

    for match in matches:
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
            roll_detail = " + ".join([str(roll) for roll in roll_results])  # Добавляем подробности о броске
            results.append(f"{display_name}, выпала 1. ({roll_detail}{modifier_display})")
            continue

        # Формируем детализированный вывод для каждого кубика
        detailed_rolls = []
        for roll in roll_results:
            if roll == 1:
                detailed_rolls.append(f"{roll}{CRIT_FAIL_EMOJI}")
            elif roll == 20 and dice_sides == 20:
                detailed_rolls.append(f"{roll}{CRIT_SUCCESS_EMOJI}")
            else:
                detailed_rolls.append(str(roll))

        # Выводим итоговый результат всех кубиков
        roll_detail = " + ".join(detailed_rolls)
        results.append(f"{display_name}, итог: {total}. ({roll_detail}{modifier_display})")

    # Если команды не найдены, выводим ошибку
    if not results:
        return f"{display_name}, в твоём сообщении не найдено команды для броска."

    return "\n".join(results)
