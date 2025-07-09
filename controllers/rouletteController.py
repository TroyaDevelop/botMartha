import random
import time
from controllers.messageController import get_user_name

class RouletteController:
    """Русская рулетка. Управляет состоянием игр в разных беседах."""

    def __init__(self):
        # games: peer_id -> state во время активной игры
        #   players         — исходный порядок (для статистики)
        #   alive_players   — порядок живых игроков; первый индекс = текущий ход
        #   current_player  — индекс в alive_players, чей сейчас ход
        #   bullet_position — в каком гнезде патрон [0..5]
        #   current_position— текущая позиция барабана [0..5]
        #   round           — номер раунда (при смерти начинается новый)
        self.games = {}

        # pending_games: peer_id -> state во время набора игроков
        #   host_id  — кто создал игру
        #   players  — список id присоединившихся
        #   timestamp— время начала набора (секунды epoch)
        self.pending_games = {}

    # -------------- Набор игроков -----------------
    def start_game(self, peer_id: int, host_id: int) -> str:
        if peer_id in self.games:
            return "Игра уже идет в этой беседе!"

        self.pending_games[peer_id] = {
            "host_id": host_id,
            "players": [host_id],
            "timestamp": time.time()
        }
        return (
            f"{get_user_name(host_id)} начинает игру в русскую рулетку! "
            "Напишите 'рулетка вступить', чтобы участвовать. У вас есть 120 секунд."
        )

    def join_game(self, peer_id: int, user_id: int) -> str:
        if peer_id not in self.pending_games:
            return "Сейчас нет активного набора в игру."

        if time.time() - self.pending_games[peer_id]["timestamp"] > 120:
            del self.pending_games[peer_id]
            return "Время набора игроков истекло."

        if user_id in self.pending_games[peer_id]["players"]:
            return "Вы уже присоединились к игре."

        self.pending_games[peer_id]["players"].append(user_id)
        players_list = [get_user_name(pid) for pid in self.pending_games[peer_id]["players"]]
        return (
            f"{get_user_name(user_id)} присоединился к своей возможно последней игре!\n"
            f"Текущие игроки: {', '.join(players_list)}. "
            "Напишите 'рулетка начать', чтобы начать игру."
        )

    # -------------- Запуск игры -----------------
    def start_roulette(self, peer_id: int) -> str:
        if peer_id not in self.pending_games:
            return "Нет игры для начала."

        if len(self.pending_games[peer_id]["players"]) < 2:
            return "Нужно минимум 2 игрока для начала."

        players = self.pending_games[peer_id]["players"]
        random.shuffle(players)  # случайный порядок ходов

        # Сохраняем состояние активной игры
        self.games[peer_id] = {
            "players": players.copy(),
            "alive_players": players.copy(),
            "current_player": 0,
            "bullet_position": random.randint(0, 5),
            "current_position": 0,
            "round": 1
        }

        del self.pending_games[peer_id]
        players_list = ", ".join(get_user_name(pid) for pid in players)
        first = get_user_name(players[0])
        return (
            "Ваша последняя игра начинается! Для выстрела напишите 'щелчок'.\n"
            f"Порядок игроков: {players_list}\n\n"
            "Раунд 1\n"
            f"Первый ход: {first}!"
        )

    # -------------- Ход игрока -----------------
    def shoot(self, peer_id: int, user_id: int) -> str:
        if peer_id not in self.games:
            return "В этой беседе нет активной игры."

        game = self.games[peer_id]

        if user_id != game["alive_players"][game["current_player"]]:
            return "Сейчас не ваш ход!"

        # Проверяем — выстрелил ли патрон
        if game["current_position"] == game["bullet_position"]:
            dead_player = game["alive_players"].pop(game["current_player"])

            # Остался последний выживший — завершение игры
            if len(game["alive_players"]) == 1:
                winner = game["alive_players"][0]
                del self.games[peer_id]
                return (
                    f"💥 БАХ! Мозги {get_user_name(dead_player)} размазались по стене!\n\n"
                    f"🏆 Победитель: {get_user_name(winner)}!"
                )

            # --- Новый раунд ---
            game["round"] += 1
            game["bullet_position"] = random.randint(0, 5)
            game["current_position"] = 0

            # ⚡️ Главное изменение: ход переходит к тому, кто следует за погибшим.
            # После pop() current_player всё ещё указывает на *следующего* игрока.
            if game["current_player"] >= len(game["alive_players"]):
                game["current_player"] = 0  # если погибший был последним в списке

            next_player_id = game["alive_players"][game["current_player"]]
            alive_list = ", ".join(get_user_name(pid) for pid in game["alive_players"])
            return (
                f"💥 БАХ! Мозги {get_user_name(dead_player)} размазались по стене!\n\n"
                f"Раунд {game['round']}\n"
                f"Оставшиеся игроки: {alive_list}\n"
                f"Первый ход: {get_user_name(next_player_id)}"
            )

        # --- Выжил, барабан вращаем дальше ---
        game["current_position"] = (game["current_position"] + 1) % 6
        game["current_player"] = (game["current_player"] + 1) % len(game["alive_players"])
        next_player = game["alive_players"][game["current_player"]]
        return f"*щелк* Выживает! Следующий ход: {get_user_name(next_player)}"
