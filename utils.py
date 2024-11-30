# Сопоставление русских названий характеристик с внутренними
stat_map = {
    "strength": "сила",
    "dexterity": "ловкость",
    "constitution": "телосложение",
    "intelligence": "интеллект",
    "wisdom": "мудрость",
    "charisma": "харизма",
    "сила": "strength",
    "ловкость": "dexterity",
    "телосложение": "constitution",
    "интеллект": "intelligence",
    "мудрость": "wisdom",
    "харизма": "charisma"
}

def calculate_modifier(score):
    """Вычисляет модификатор для характеристики в D&D 5e."""
    return (score - 10) // 2

# def set_hp(constitution, char_class):
  #  if char_class == "Варвар":
   #     return 12 + calculate_modifier(constitution)
