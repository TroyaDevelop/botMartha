import random
import re
from typing import List, Dict, Set, Optional

# ====== Глобальные настройки ======
MAX_DICE_COUNT = 250      # максимальное число одновременно бросаемых кубиков
MAX_DICE_SIDES = 1000      # максимальное число граней у кубика
BIAS_EXPONENT  = 0.8      # < 1.0 — чаще высокие значения, > 1.0 — чаще низкие

CRIT_FAIL_EMOJI    = "☠️"
CRIT_SUCCESS_EMOJI = "💥"
GEAR_EMOJI         = "⚙️"

# Критические диапазоны: ключ = граней, значения = множества «success»/«fail»
CRITICAL_RANGES: Dict[int, Dict[str, Set[int]]] = {
    20: {"success": {20}, "fail": {1}},
    16: {"success": {16}},
    12: {"success": {12}},
    10: {"success": {10}},
     8: {"success": {8}},
     6: {"success": {6},  "fail": {1}},
}

# ====== Справка ======
dice_help_message = (
    "Здравствуй, авантюрист! Я помогу тебе разобраться с системой бросков кубиков:\n\n"
    "🎲 Команды бросков:\n"
    "- /д20 — бросить один 20‑гранный кубик.\n"
    "- /3д6 — бросить три 6‑гранных кубика и показать сумму.\n"
    "- /д20+5 — бросить один 20‑гранный кубик и добавить модификатор +5.\n"
    "- /д20^ — бросок с преимуществом (лучший из двух d20).\n"
    "- /д20_ — бросок с помехой (худший из двух d20).\n\n"
    "Криты: 💥 при значениях из таблицы крит‑успехов, ☠️ — крит‑провал.\n"
    "Напиши 'помощь', если понадобится эта инструкция ещё раз. Удачи в бросках! 🎲"
)

# ====== Вспомогательные функции ======

def biased_roll(
    sides: int,
    exponent: float = BIAS_EXPONENT,
    rng: Optional[random.Random] = None,
) -> int:
    """Возвращает *одно* значение кубика c управляемым смещением.

    Параметр *exponent* контролирует кривизну распределения:
        • **1.0**  — равномерная вероятность (стандартный куб).
        • **< 1.0** — увеличивает шанс *высоких* чисел (0.8 ≈ +10 % к старшим граням).
        • **> 1.0** — увеличивает шанс *низких* чисел (1.2 ≈ +10 % к младшим граням).

    Можно передать собственный RNG (например, :class:`random.SystemRandom`) —
    это облегчает юнит‑тестирование и позволяет, при желании, использовать
    криптографически стойкий генератор.
    """
    if sides < 2:
        raise ValueError("sides must be ≥ 2")
    if exponent <= 0:
        raise ValueError("exponent must be > 0")

    rng = rng or random
    u = rng.random()              # 0 ≤ u < 1
    v = u ** exponent             # степенное преобразование
    result = int(v * sides) + 1   # 1 … sides (включительно)
    return min(result, sides)     # защита от округления «sides + 1»


def roll_dice(
    sides: int,
    rolls: int = 1,
    exponent: float = BIAS_EXPONENT,
    rng: Optional[random.Random] = None,
) -> List[int]:
    """Бросает *rolls* раз кубик на *sides* граней с тем же смещением."""
    return [biased_roll(sides, exponent, rng) for _ in range(rolls)]


def _crit_emoji(roll: int, sides: int) -> str:
    """Возвращает строку с эмодзи крит‑успеха/провала (если применимо)."""
    cfg = CRITICAL_RANGES.get(sides, {})
    if roll in cfg.get("fail", set()) or (roll == 1 and sides not in cfg.get("success", set())):
        return f" {CRIT_FAIL_EMOJI}"
    if roll in cfg.get("success", set()):
        return f" {CRIT_SUCCESS_EMOJI}"
    return ""

# ====== Основной контроллер ======

def calculate_roll(nickname: str, command: str) -> str:
    """Разбирает текст *command* и возвращает результат броска кубиков."""
    normalized = command.replace("к", "д").replace("d", "д").strip()
    if not normalized:
        return f"Да, {nickname}?"

    low = normalized.lower()
    if "/помощь" in low or "помощь" in low:
        return dice_help_message
    if "поцелуй" in low:
        return "😘"

    #  /2д6+3      /д20^     /4д8_-1
    dice_re = re.compile(
        r"(?P<count>\d*)д(?P<sides>\d+)(?P<adv>[\^_]?)"
        r"((?P<modifiers>([+-]\d+)+))?"
    )
    mod_re = re.compile(r"([+-]\d+)")

    out_lines: List[str] = []

    for m in dice_re.finditer(normalized):
        dice_count = int(m.group("count") or "1")
        dice_sides = int(m.group("sides"))
        adv_flag   = m.group("adv")

        # ---- Валидация ----
        if dice_count > MAX_DICE_COUNT or dice_sides > MAX_DICE_SIDES or dice_sides < 2:
            out_lines.append(f"Слишком много кубиков или граней, {nickname}.")
            continue
        if adv_flag and dice_count != 1:
            out_lines.append(f"Advantage/Disadvantage допустимы только для одного кубика, {nickname}.")
            continue

        # ---- Модификаторы ----
        mods_str  = m.group("modifiers") or ""
        mod_vals  = [int(x) for x in mod_re.findall(mods_str)]
        total_mod = sum(mod_vals)
        mod_disp  = f" {'+' if total_mod>=0 else '-'} {abs(total_mod)} {GEAR_EMOJI}" if mods_str else ""

        # ---- Бросок ----
        if adv_flag:
            pair    = roll_dice(dice_sides, 2)
            chosen  = max(pair) if adv_flag == "^" else min(pair)
            total   = chosen + total_mod
            detail  = f"{pair[0]} / {pair[1]} → {chosen}{_crit_emoji(chosen, dice_sides)}{mod_disp}"
            out_lines.append(f"{nickname}, итог: {total}. ({detail})")
            continue

        # Обычный бросок / несколько кубов
        rolls  = roll_dice(dice_sides, dice_count)
        total  = sum(rolls) + total_mod
        detailed = " + ".join(f"{r}{_crit_emoji(r, dice_sides)}" for r in rolls)
        out_lines.append(f"{nickname}, итог: {total}. ({detailed}{mod_disp})")

    if not out_lines:
        return f"{nickname}, в твоём сообщении не найдено команды для броска."

    return "\n".join(out_lines)
