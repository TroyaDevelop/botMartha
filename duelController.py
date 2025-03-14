import random
import time
import json
from messageController import get_user_name

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
        try:
            with open('duel_stats.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_stats(stats):
        with open('duel_stats.json', 'w', encoding='utf-8') as file:
            json.dump(stats, file, ensure_ascii=False, indent=4)

    @staticmethod
    def update_stats(peer_id, winner_id):
        stats = DuelController.load_stats()
        if str(peer_id) not in stats:
            stats[str(peer_id)] = {}
        if str(winner_id) not in stats[str(peer_id)]:
            stats[str(peer_id)][str(winner_id)] = 0
        stats[str(peer_id)][str(winner_id)] += 1
        DuelController.save_stats(stats)

    @staticmethod
    def get_stats(peer_id):
        stats = DuelController.load_stats()
        return stats.get(str(peer_id), {})

    @staticmethod
    def get_rank(wins):
        ranks = {
            0: 'Новичок😀',
            5: 'Дуэлянт🤺',
            20: 'Злодей😈',
            50: 'Убийца☠️',
            100: 'Маньяк🔪',
            200: 'Потрошитель💀',
            500: 'Бастер Скраггс🔫',
            1000: 'Авантюрист🏴‍☠️'
        }
        for threshold, rank in sorted(ranks.items(), reverse=True):
            if wins >= threshold:
                return rank
        return 'Новичок'

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
            del duels[duel.players[0]]
            del duels[duel.players[1]]
            DuelController.update_stats(peer_id, winner)
            winner_name = get_user_name(winner)
            return f'Попадание!💥 Победитель: {winner_name}.'
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
