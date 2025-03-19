import random
import time
import json
import os
from controllers.messageController import get_user_name
from controllers.profileController import ProfileController
profile_controller = ProfileController()

class DuelController:
    def __init__(self, player1_id, player2_id):
        self.players = [player1_id, player2_id]
        self.current_turn = random.choice([0, 1])
        self.winner = None
        self.last_shot_time = time.time()

    def shoot(self):
        hit = random.choice([True, False])
        if hit:
            self.winner = self.players[self.current_turn]
        self.current_turn = 1 - self.current_turn
        self.last_shot_time = time.time()
        return hit, self.winner

    def get_current_player(self):
        return self.players[self.current_turn]

    def is_timed_out(self):
        return time.time() - self.last_shot_time > 120

    @staticmethod
    def load_stats():
        if not os.path.exists('data/duel_stats.json'):
            with open('data/duel_stats.json', 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        with open('data/duel_stats.json', 'r', encoding='utf-8') as file:
            return json.load(file)

    @staticmethod
    def save_stats(stats):
        with open('data/duel_stats.json', 'w', encoding='utf-8') as file:
            json.dump(stats, file, ensure_ascii=False, indent=4)

    @staticmethod
    def update_stats(peer_id, winner_id, loser_id):
        stats = DuelController.load_stats()
        if str(peer_id) not in stats:
            stats[str(peer_id)] = {}
        if str(winner_id) not in stats[str(peer_id)]:
            stats[str(peer_id)][str(winner_id)] = {"wins": 0, "streak": 0}
        if str(loser_id) not in stats[str(peer_id)]:
            stats[str(peer_id)][str(loser_id)] = {"wins": 0, "streak": 0}
        
        # Увеличиваем счетчик побед и streak для победителя
        stats[str(peer_id)][str(winner_id)]["wins"] += 1
        stats[str(peer_id)][str(winner_id)]["streak"] += 1
        
        # Сбрасываем streak проигравшего
        stats[str(peer_id)][str(loser_id)]["streak"] = 0
        
        DuelController.save_stats(stats)
        return stats[str(peer_id)][str(winner_id)]["streak"]

    @staticmethod
    def get_stats(peer_id):
        stats = DuelController.load_stats()
        peer_stats = stats.get(str(peer_id), {})
        if peer_stats:
            # Сортировка только по количеству побед
            sorted_stats = sorted(
                peer_stats.items(),
                key=lambda x: x[1]["wins"],
                reverse=True
            )
            return dict(sorted_stats)
        return {}

    @staticmethod
    def get_duel_stats():
        with open('data/duel_stats.json', 'r', encoding='utf-8') as file:
            stats = json.load(file)
        
        # Сортировка по количеству убийств (по убыванию)
        sorted_stats = sorted(stats.items(), key=lambda x: sum(x[1].values()), reverse=True)
        
        return dict(sorted_stats)

    @staticmethod
    def get_rank(wins):
        ranks = {
            0: 'Пацифист😀',
            1: 'Грязнуля🙂',
            5: 'Психованный😐',
            20: 'Буйный😠',
            50: 'Яростный😡',
            100: 'Убийца🤬',
            200: 'Доминатор👿',
            500: 'Неостановимый😈',
            1000: 'Богоподобный☠️',
            2000: 'V2🤖🟥',
            4000: 'V1🤖🟦',
            6000: 'Чемпион смерти☠️',
            8000: 'Ангел смерти☠️',
            9999: 'Сама смерть☠️',
        }
        for threshold, rank in sorted(ranks.items(), reverse=True):
            if wins >= threshold:
                return rank
        return 'Пацифист'

    @staticmethod
    def handle_duel_command(user_id, reply_message=None):
        if reply_message:
            opponent_id = reply_message['from_id']
            if user_id == opponent_id:
                return 'Нельзя дуэлиться с самим собой!'
            pending_duels[opponent_id] = {'challenger': user_id, 'timestamp': time.time()}
            user_name = get_user_name(user_id)
            return f'Пользователь {user_name} вызывает вас на дуэль! Ответьте "принять дуэль", чтобы начать.'
        else:
            return 'Ответьте на сообщение пользователя, чтобы вызвать его на дуэль.'

    @staticmethod
    def handle_accept_duel(user_id):
        if user_id in pending_duels:
            if time.time() - pending_duels[user_id]['timestamp'] > 60:
                del pending_duels[user_id]
                return 'Время на принятие дуэли истекло.'
            opponent_id = pending_duels[user_id]['challenger']
            if opponent_id in duels:
                return 'Дуэль уже началась.'
            duel = DuelController(opponent_id, user_id)
            duels[user_id] = duel
            duels[opponent_id] = duel
            del pending_duels[user_id]
            user_name = get_user_name(user_id)
            opponent_name = get_user_name(opponent_id)
            return f'Дуэль началась! {opponent_name} против {user_name}. Первый ход за {get_user_name(duel.get_current_player())}.'
        else:
            return 'Вас никто не вызывал на дуэль.'

    @staticmethod
    def handle_shoot_command(peer_id, user_id):
        if user_id not in duels:
            return 'Вы не участвуете в дуэли.'
        duel = duels[user_id]
        if duel.get_current_player() != user_id:
            return 'Сейчас не ваш ход.'
        hit, winner = duel.shoot()
        if winner:
            loser = duel.players[0] if winner == duel.players[1] else duel.players[1]
            del duels[duel.players[0]]
            del duels[duel.players[1]]
            current_streak = DuelController.update_stats(peer_id, winner, loser)
            winner_name = get_user_name(winner)
            streak_msg = f"\nСерия убийств: {current_streak}🔥" if current_streak > 1 else ""
            return f'Попадание!💥 Победитель: {winner_name}.{streak_msg}'
        else:
            next_player_name = get_user_name(duel.get_current_player())
            return f'Промах!❌ Ход переходит к {next_player_name}.'

    @staticmethod
    def check_timeouts():
        for user_id, duel in list(duels.items()):
            if duel.is_timed_out():
                del duels[duel.players[0]]
                del duels[duel.players[1]]
                return f'Дуэль завершена. {get_user_name(duel.players[0])} и {get_user_name(duel.players[1])} не сделали выстрел вовремя.'
        return None

duels = {}
pending_duels = {}
