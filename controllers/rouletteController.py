import random
import time
from controllers.messageController import get_user_name

class RouletteController:
    def __init__(self):
        self.games = {}  # {peer_id: {players: [], alive_players: [], current_player: 0, bullet_position: int}}
        self.pending_games = {}  # {peer_id: {host_id: id, players: [], timestamp: float}}

    def start_game(self, peer_id, host_id):
        if peer_id in self.games:
            return "Игра уже идет в этой беседе!"
        
        self.pending_games[peer_id] = {
            "host_id": host_id,
            "players": [host_id],
            "timestamp": time.time()
        }
        return f"{get_user_name(host_id)} начинает игру в русскую рулетку! Напишите 'рулетка присоединиться', чтобы участвовать. У вас есть 60 секунд."

    def join_game(self, peer_id, user_id):
        if peer_id not in self.pending_games:
            return "Сейчас нет активного набора в игру."
        
        if time.time() - self.pending_games[peer_id]["timestamp"] > 60:
            del self.pending_games[peer_id]
            return "Время набора игроков истекло."

        if user_id in self.pending_games[peer_id]["players"]:
            return "Вы уже присоединились к игре."

        self.pending_games[peer_id]["players"].append(user_id)
        players_list = [get_user_name(pid) for pid in self.pending_games[peer_id]["players"]]
        return f"{get_user_name(user_id)} присоединился к своей возможно последней игре!\nТекущие игроки: {', '.join(players_list)}. Напишите 'рулетка начать', чтобы начать игру."

    def start_roulette(self, peer_id):
        if peer_id not in self.pending_games:
            return "Нет игры для начала."
            
        if len(self.pending_games[peer_id]["players"]) < 2:
            return "Нужно минимум 2 игрока для начала."

        players = self.pending_games[peer_id]["players"]
        random.shuffle(players)  # Перемешиваем порядок игроков
        
        self.games[peer_id] = {
            "players": players.copy(),  # Сохраняем список всех игроков
            "alive_players": players.copy(),  # Список живых игроков
            "current_player": 0,
            "bullet_position": random.randint(0, 5),
            "current_position": 0,
            "round": 1  # Добавляем счетчик раундов
        }
        
        del self.pending_games[peer_id]
        players_list = [get_user_name(pid) for pid in players]
        return f"Ваша последняя игра начинается! Порядок игроков:\n{', '.join(players_list)}\n\nРаунд 1\nПервый ход: {get_user_name(players[0])}!"

    def shoot(self, peer_id, user_id):
        if peer_id not in self.games:
            return "В этой беседе нет активной игры."
            
        game = self.games[peer_id]
        if user_id != game["alive_players"][game["current_player"]]:
            return "Сейчас не ваш ход!"

        # Проверяем, попала ли пуля
        if game["current_position"] == game["bullet_position"]:
            dead_player = game["alive_players"][game["current_player"]]
            # Убираем игрока из списка живых
            game["alive_players"].pop(game["current_player"])
            
            # Проверяем, остался ли только один игрок
            if len(game["alive_players"]) == 1:
                winner = game["alive_players"][0]
                del self.games[peer_id]
                return (f"💥 БАХ! Мозги{get_user_name(dead_player)}размазались по стене!\n\n"
                       f"🏆 Победитель: {get_user_name(winner)}!")
            
            # Если игроков больше одного, начинаем новый раунд
            game["round"] += 1
            game["bullet_position"] = random.randint(0, 5)
            game["current_position"] = 0
            game["current_player"] = 0
            
            alive_list = [get_user_name(pid) for pid in game["alive_players"]]
            return (f"💥 БАХ! Мозги{get_user_name(dead_player)}размазались по стене!\n\n"
                   f"Раунд {game['round']}\n"
                   f"Оставшиеся игроки: {', '.join(alive_list)}\n"
                   f"Первый ход: {get_user_name(game['alive_players'][0])}")
        
        # Переходим к следующему живому игроку
        game["current_position"] = (game["current_position"] + 1) % 6
        game["current_player"] = (game["current_player"] + 1) % len(game["alive_players"])
        next_player = game["alive_players"][game["current_player"]]
        
        return f"*щелк* Выживает! Следующий ход: {get_user_name(next_player)}"