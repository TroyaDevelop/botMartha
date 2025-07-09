import json
import os
import math
from controllers.messageController import get_user_name

class CharacterController:
    def __init__(self):
        self.characters = self.load_characters()
        # Допустимые классы D&D 5e
        self.dnd_classes = [
            "Бард", "Варвар", "Воин", "Волшебник", "Друид", "Жрец", 
            "Колдун", "Монах", "Паладин", "Плут", "Следопыт", "Чародей"
        ]
        # Допустимые расы D&D 5e
        self.dnd_races = [
            "Человек", "Эльф", "Дварф", "Полурослик", "Гном", "Полуорк", 
            "Полуэльф", "Тифлинг", "Драконорожденный", "Табакси", "Аасимар", "Голиаф"
        ]
        # Допустимое мировоззрение
        self.alignments = [
            "Законно-добрый", "Нейтрально-добрый", "Хаотично-добрый",
            "Законно-нейтральный", "Нейтральный", "Хаотично-нейтральный",
            "Законно-злой", "Нейтрально-злой", "Хаотично-злой"
        ]
        # Навыки и соответствующие им характеристики
        self.skills = {
            "Акробатика": "dexterity",
            "Анализ": "intelligence",
            "Атлетика": "strength",
            "Восприятие": "wisdom",
            "Выживание": "wisdom",
            "Выступление": "charisma",
            "Запугивание": "charisma",
            "История": "intelligence",
            "Ловкость рук": "dexterity",
            "Магия": "intelligence",
            "Медицина": "wisdom",
            "Обман": "charisma",
            "Природа": "intelligence",
            "Проницательность": "wisdom",
            "Религия": "intelligence",
            "Скрытность": "dexterity",
            "Убеждение": "charisma",
            "Уход за животными": "wisdom"
        }
        # Наборы спасбросков для каждого класса
        self.saving_throws = {
            "Бард": ["dexterity", "charisma"],
            "Варвар": ["strength", "constitution"],
            "Воин": ["strength", "constitution"],
            "Волшебник": ["intelligence", "wisdom"],
            "Друид": ["intelligence", "wisdom"],
            "Жрец": ["wisdom", "charisma"],
            "Колдун": ["wisdom", "charisma"],
            "Монах": ["strength", "dexterity"],
            "Паладин": ["wisdom", "charisma"],
            "Плут": ["dexterity", "intelligence"],
            "Следопыт": ["strength", "dexterity"],
            "Чародей": ["constitution", "charisma"]
        }
        # Перевод характеристик с английского на русский
        self.stat_names = {
            "strength": "Сила",
            "dexterity": "Ловкость",
            "constitution": "Телосложение",
            "intelligence": "Интеллект",
            "wisdom": "Мудрость",
            "charisma": "Харизма"
        }
        # Диалоговые состояния для интерактивного создания персонажа
        self.dialog_states = {}
    
    def load_characters(self):
        """Загружает персонажей из файла."""
        if not os.path.exists('data/characters.json'):
            with open('data/characters.json', 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        with open('data/characters.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_characters(self):
        """Сохраняет персонажей в файл."""
        with open('data/characters.json', 'w', encoding='utf-8') as f:
            json.dump(self.characters, f, ensure_ascii=False, indent=4)
    
    def start_character_creation(self, user_id, peer_id):
        """Начинает процесс создания персонажа."""
        self.characters = self.load_characters()
        user_id_str = str(user_id)
        
        # Проверяем, есть ли у пользователя уже персонаж (в любой беседе)
        if user_id_str in self.characters:
            return "Вы уже участник гильдии! Напишите 'лицензия' чтобы увидеть своего персонажа или 'сдать лицензию' чтобы удалить его."
        
        # Инициализируем диалоговое состояние
        self.dialog_states[user_id] = {
            "state": "ask_name",
            "peer_id": peer_id,
            "character": {
                "name": "",
                "class": "",
                "race": "",
                "level": 1,
                "alignment": "",
                "stats": {
                    "strength": 10,
                    "dexterity": 10,
                    "constitution": 10,
                    "intelligence": 10,
                    "wisdom": 10,
                    "charisma": 10
                },
                "proficiency_bonus": 2,
                "hp": 0,
                "max_hp": 0,
                "skills": {},
                "saving_throws": {},
                "background": "",
                "inventory": [],
                "spells": [],
                "features": [],
                "ac": 10,  # Базовая броня без доспехов
                "initiative": 0,
                "speed": 30,  # Стандартная скорость
                "hit_dice": ""
            }
        }
        
        return "Как ваше имя, авантюрист? Напишите его, чтобы начать создание персонажа."
    
    def process_character_creation(self, user_id, text):
        """Обрабатывает ответы пользователя в процессе создания персонажа."""
        if user_id not in self.dialog_states:
            return None
        
        dialog = self.dialog_states[user_id]
        state = dialog["state"]
        character = dialog["character"]
        
        # Обработка различных состояний диалога
        if state == "ask_name":
            character["name"] = text.strip()
            dialog["state"] = "ask_race"
            return f"Отлично, {character['name']}! Выберите расу персонажа:\n" + "\n".join(self.dnd_races)
        
        elif state == "ask_race":
            text_lower = text.lower().strip()
            for race in self.dnd_races:
                if race.lower() == text_lower:
                    character["race"] = race
                    dialog["state"] = "ask_class"
                    return f"Ваша раса: {race}. Теперь выберите класс персонажа:\n" + "\n".join(self.dnd_classes)
            return "Пожалуйста, выберите расу из списка:\n" + "\n".join(self.dnd_races)
        
        elif state == "ask_class":
            text_lower = text.lower().strip()
            for dnd_class in self.dnd_classes:
                if dnd_class.lower() == text_lower:
                    character["class"] = dnd_class
                    character["hit_dice"] = self.get_hit_dice(dnd_class)
                    
                    # Устанавливаем владение спасбросками для класса
                    saving_throws = self.saving_throws.get(dnd_class, [])
                    for stat in saving_throws:
                        character["saving_throws"][stat] = True
                    
                    dialog["state"] = "ask_alignment"
                    return f"Ваш класс: {dnd_class}. Выберите мировоззрение персонажа:\n" + "\n".join(self.alignments)
            return "Пожалуйста, выберите класс из списка:\n" + "\n".join(self.dnd_classes)
        
        elif state == "ask_alignment":
            text_lower = text.lower().strip()
            for alignment in self.alignments:
                if alignment.lower() == text_lower:
                    character["alignment"] = alignment
                    dialog["state"] = "ask_stats"
                    return (
                        f"Ваше мировоззрение: {alignment}. Теперь давайте определим характеристики персонажа.\n\n"
                        "Введите 6 чисел через пробел для определения следующих характеристик:\n"
                        "Сила, Ловкость, Телосложение, Интеллект, Мудрость, Харизма.\n\n"
                        "Например: 15 14 13 12 10 8"
                    )
            return "Пожалуйста, выберите мировоззрение из списка:\n" + "\n".join(self.alignments)
        
        elif state == "ask_stats":
            try:
                stats = [int(n) for n in text.split()]
                if len(stats) != 6:
                    return "Пожалуйста, введите ровно 6 чисел для характеристик."
                
                # Устанавливаем значения характеристик
                stat_keys = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
                for i, stat_key in enumerate(stat_keys):
                    character["stats"][stat_key] = stats[i]
                
                # Вычисляем бонусы характеристик
                stat_bonuses = {
                    stat: math.floor((value - 10) / 2)
                    for stat, value in character["stats"].items()
                }
                
                # Рассчитываем здоровье персонажа
                hit_dice_num = int(character["hit_dice"].split('d')[1])
                character["max_hp"] = hit_dice_num + stat_bonuses["constitution"]
                character["hp"] = character["max_hp"]
                
                # Устанавливаем инициативу
                character["initiative"] = stat_bonuses["dexterity"]
                
                # Устанавливаем КД (Класс Брони)
                character["ac"] = 10 + stat_bonuses["dexterity"]
                
                dialog["state"] = "ask_skills"
                return self.get_skills_selection_message(character["class"])
            
            except ValueError:
                return "Пожалуйста, введите 6 чисел, разделенных пробелами."
        
        elif state == "ask_skills":
            skills_to_choose = text.split(",")
            skills_to_choose = [skill.strip() for skill in skills_to_choose]
            
            # Проверяем, все ли выбранные навыки допустимы
            valid_skills = True
            for skill in skills_to_choose:
                if skill not in self.skills:
                    valid_skills = False
                    break
            
            if valid_skills:
                # Устанавливаем владение выбранными навыками
                for skill in skills_to_choose:
                    character["skills"][skill] = True
                
                dialog["state"] = "ask_background"
                return "Отлично! Теперь введите предысторию вашего персонажа."
            else:
                return f"Пожалуйста, выберите навыки из списка, разделяя их запятыми:\n{', '.join(self.skills.keys())}"
        
        elif state == "ask_background":
            character["background"] = text.strip()
            
            # Завершаем создание персонажа - пропускаем запросы на черты личности, идеалы, привязанности и недостатки
            user_id_str = str(user_id)
            
            # Сохраняем персонажа в базу данных
            self.characters[user_id_str] = character
            self.save_characters()
            
            # Удаляем диалоговое состояние
            del self.dialog_states[user_id]
            
            return f"Поздравляю! Ваш персонаж {character['name']} ({character['race']} {character['class']}) создан!\n\nЧтобы увидеть лист персонажа, введите команду 'лицензия'."
    
    def get_hit_dice(self, dnd_class):
        """Возвращает кубик хитов для класса."""
        hit_dice_map = {
            "Варвар": "1d12",
            "Воин": "1d10",
            "Паладин": "1d10",
            "Следопыт": "1d10",
            "Бард": "1d8",
            "Жрец": "1d8",
            "Друид": "1d8",
            "Монах": "1d8",
            "Плут": "1d8",
            "Волшебник": "1d6",
            "Чародей": "1d6",
            "Колдун": "1d8"
        }
        return hit_dice_map.get(dnd_class, "1d8")
    
    def get_skills_selection_message(self, dnd_class):
        """Возвращает сообщение с выбором навыков для класса."""
        class_skills = {
            "Бард": ["Выберите любые 3 навыка"],
            "Варвар": ["Выберите 2 из: Атлетика, Восприятие, Выживание, Запугивание, Природа, Уход за животными"],
            "Воин": ["Выберите 2 из: Акробатика, Атлетика, Восприятие, Выживание, Запугивание, История, Проницательность, Уход за животными"],
            "Волшебник": ["Выберите 2 из: Анализ, История, Магия, Медицина, Проницательность, Религия"],
            "Друид": ["Выберите 2 из: Восприятие, Выживание, Магия, Медицина, Природа, Проницательность, Религия, Уход за животными"],
            "Жрец": ["Выберите 2 из: История, Медицина, Проницательность, Религия, Убеждение"],
            "Колдун": ["Выберите 2 из: Анализ, История, Запугивание, Магия, Обман, Природа, Религия"],
            "Монах": ["Выберите 2 из: Акробатика, Атлетика, История, Проницательность, Религия, Скрытность"],
            "Паладин": ["Выберите 2 из: Атлетика, Запугивание, Медицина, Проницательность, Религия, Убеждение"],
            "Плут": ["Выберите 4 из: Акробатика, Анализ, Атлетика, Восприятие, Выступление, Запугивание, Ловкость рук, Обман, Проницательность, Скрытность, Убеждение"],
            "Следопыт": ["Выберите 3 из: Атлетика, Восприятие, Выживание, Запугивание, Природа, Проницательность, Скрытность, Уход за животными"],
            "Чародей": ["Выберите 2 из: Запугивание, Магия, Обман, Проницательность, Религия, Убеждение"]
        }
        
        message = class_skills.get(dnd_class, ["Выберите 2 любых навыка"])[0]
        message += "\n\nВведите выбранные навыки через запятую, например: Атлетика, Восприятие, Выживание"
        
        return message
    
    def get_character_sheet(self, user_id, peer_id):
        """Возвращает лист персонажа пользователя."""
        self.characters = self.load_characters()
        user_id_str = str(user_id)
        
        if user_id_str not in self.characters:
            return "У вас нет персонажа. Используйте команду 'создать персонажа', чтобы начать."
        
        character = self.characters[user_id_str]
        
        # Вычисляем бонусы характеристик
        stat_bonuses = {
            stat: math.floor((value - 10) / 2)
            for stat, value in character["stats"].items()
        }
        
        # Формируем лист персонажа
        sheet = f"📜 Лист персонажа: {character['name']}\n"
        sheet += f"🧝 Раса: {character['race']}\n"
        sheet += f"⚔️ Класс: {character['class']} (Уровень {character['level']})\n"
        sheet += f"🔮 Мировоззрение: {character['alignment']}\n\n"
        
        # Характеристики
        sheet += "📊 Характеристики:\n"
        for stat, value in character["stats"].items():
            bonus = stat_bonuses[stat]
            bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)
            sheet += f"{self.stat_names[stat]}: {value} ({bonus_str})\n"
        
        sheet += f"\n❤️ Здоровье: {character['hp']}/{character['max_hp']}\n"
        sheet += f"🛡️ КД: {character['ac']}\n"
        sheet += f"⚡ Инициатива: {'+' if character['initiative'] >= 0 else ''}{character['initiative']}\n"
        sheet += f"👣 Скорость: {character['speed']} футов\n"
        sheet += f"🎲 Кость хитов: {character['hit_dice']}\n"
        sheet += f"🏆 Бонус мастерства: +{character['proficiency_bonus']}\n\n"
        
        # Спасброски
        sheet += "🛡️ Спасброски:\n"
        for stat, name in self.stat_names.items():
            is_proficient = stat in character.get("saving_throws", {})
            bonus = stat_bonuses[stat] + (character["proficiency_bonus"] if is_proficient else 0)
            bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)
            prof_mark = "✓" if is_proficient else " "
            sheet += f"[{prof_mark}] {name}: {bonus_str}\n"
        
        # Навыки
        sheet += "\n🔧 Навыки:\n"
        for skill, stat in self.skills.items():
            is_proficient = skill in character.get("skills", {})
            bonus = stat_bonuses[stat] + (character["proficiency_bonus"] if is_proficient else 0)
            bonus_str = f"+{bonus}" if bonus >= 0 else str(bonus)
            prof_mark = "✓" if is_proficient else " "
            sheet += f"[{prof_mark}] {skill} ({self.stat_names[stat][0:3]}): {bonus_str}\n"
        
        # Только предыстория без черт характера, идеалов, привязанностей и недостатков
        sheet += f"\n📚 Предыстория: {character['background']}\n"
        
        return sheet
    
    def delete_character(self, user_id, peer_id):
        """Удаляет персонажа пользователя."""
        self.characters = self.load_characters()
        user_id_str = str(user_id)
        
        if user_id_str not in self.characters:
            return "У вас нет персонажа."
        
        character_name = self.characters[user_id_str]["name"]
        del self.characters[user_id_str]
        self.save_characters()
        
        return f"Персонаж {character_name} удален."
    
    def is_in_character_creation(self, user_id):
        """Проверяет, находится ли пользователь в процессе создания персонажа."""
        return user_id in self.dialog_states
    
    def reset_character_creation(self, user_id):
        """Отменяет процесс создания персонажа."""
        if user_id in self.dialog_states:
            del self.dialog_states[user_id]
            return "Процесс создания персонажа отменен."
        return "Вы не находитесь в процессе создания персонажа."