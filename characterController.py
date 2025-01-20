import json
from logging.config import valid_ident

from config import editable_stats
from utils import stat_map, calculate_modifier

character_sheets = {}

def create_character(user_id, name, race, char_class):
    character_sheets[user_id] = {
        "name": name,
        "race": race,
        "class": char_class,
        "level": 1,
        "hp" : 10,
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        "inventory": [],
    }
    save_characters()
    return f"Добро пожаловать в гильдию авантюристов, господин {name}."

def update_character_stat(user_id, stat, value):
    global character_sheets
    user_id = str(user_id)
    character = character_sheets.get(user_id)
    if stat not in editable_stats:
        return f"Характеристика '{stat}' недопустима для изменения."

    try:
        value = int(value)
        character[stat] = value
        # character_sheets[user_id]["hp"] = set_hp(character_sheets[user_id]["constitution"], character_sheets[user_id]["class"])
        stat_russian = stat_map.get(stat, stat)
        save_characters()
        return f"Характеристика '{stat_russian}' обновлена на {value}!"
    except ValueError:
        return "Пожалуйста, введите числовое значение для характеристики."

def show_character(user_id):
    character = character_sheets.get(str(user_id))
    if not character:
        return "К сожалению, вы не состоите в гильдии авантюристов."

    # Создаем строки с характеристиками и модификаторами
    strength = character["strength"]
    dexterity = character["dexterity"]
    constitution = character.get("constitution", 10)
    intelligence = character.get("intelligence", 10)
    wisdom = character.get("wisdom", 10)
    charisma = character.get("charisma", 10)

    return (
        f"Персонаж: {character['name']}\n"
        f"Раса: {character['race']}\n"
        f"Класс: {character['class']}\n"
        f"Уровень: {character['level']}\n\n"
        f"Хиты: {character['hp']}\n\n"
        f"Сила: {strength} ({calculate_modifier(strength):+})\n"
        f"Ловкость: {dexterity} ({calculate_modifier(dexterity):+})\n"
        f"Телосложение: {constitution} ({calculate_modifier(constitution):+})\n"
        f"Интеллект: {intelligence} ({calculate_modifier(intelligence):+})\n"
        f"Мудрость: {wisdom} ({calculate_modifier(wisdom):+})\n"
        f"Харизма: {charisma} ({calculate_modifier(charisma):+})"
)


def updateInv(user_id, item_name, quantity):
    character = character_sheets.get(str(user_id))
    if not character:
        return "К сожалению, вы не состоите в гильдии авантюристов."

    inventory = character["inventory"]

    # Проверка на существование предмета в инвентаре
    for item in inventory:
        if item["item"].lower() == item_name.lower():  # Сравнение без учёта регистра
            item["quantity"] += quantity  # Увеличиваем количество
            save_characters()
            return f"Добавлено {quantity}x '{item_name}' в инвентарь."

    # Если предмет не найден, добавляем новый
    inventory.append({"item": item_name, "quantity": quantity})
    save_characters()
    return f"Добавлено {quantity}x '{item_name}' в инвентарь."


def showInv(user_id):
    character = character_sheets.get(str(user_id))
    if not character:
        return "К сожалению, вы не состоите в гильдии авантюристов."
    try:
        inventory = character["inventory"]
        if len(inventory) == 0:
            return "Инвентарь пуст."
        else:
            return "\n".join([f"{item['item']} ({item['quantity']} шт.)" for item in inventory])
    except ValueError:
        return "Не удалось получить инвентарь."


def delInv(user_id, item_name, quantity):
    character = character_sheets.get(str(user_id))
    if not character:
        return "К сожалению, вы не состоите в гильдии авантюристов."

    inventory = character["inventory"]
    item_found = False

    for item in inventory:
        if item["item"].lower() == item_name.lower():  # Сравнение без учёта регистра
            item_found = True
            if item["quantity"] >= quantity:
                item["quantity"] -= quantity
                if item["quantity"] == 0:
                    inventory.remove(item)  # Удаление предмета, если его количество стало 0
                save_characters()
                return f"Удалено {quantity}x '{item_name}' из инвентаря."
            else:
                return f"В вашем инвентаре недостаточно {item_name}. Доступно: {item['quantity']}."

    if not item_found:
        return f"Предмет '{item_name}' не найден в вашем инвентаре."

    save_characters()  # Сохраняем изменения после удаления
    return "Ошибка при удалении предмета из инвентаря."


def load_characters(filename="characters.json"):
    global character_sheets
    try:
        with open(filename, "r", encoding="utf-8") as file:
            character_sheets = json.load(file)  # Загружаем данные в глобальную переменную
            print("Персонажи успешно загружены.")
            print(character_sheets)  # Печать для проверки
            return character_sheets
    except (FileNotFoundError, json.JSONDecodeError):
        print("Файл не найден или поврежден. Начинаем с пустого списка персонажей.")
        character_sheets = {}
        return character_sheets

def save_characters(filename="characters.json"):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(character_sheets, file, ensure_ascii=False, indent=4)
        print("Персонажи успешно сохранены.")
    except Exception as e:
        print(f"Ошибка при сохранении персонажей: {e}")