import random
from messageController import get_user_name

class DuelController:
    def __init__(self, player1_id, player2_id):
        self.players = [player1_id, player2_id]
        self.current_turn = 0
        self.winner = None

    def shoot(self):
        hit = random.choice([True, False])
        if hit:
            self.winner = self.players[self.current_turn]
        self.current_turn = 1 - self.current_turn
        return hit, self.winner

    def get_current_player(self):
        return self.players[self.current_turn]

    @staticmethod
    def handle_duel_command(user_id, reply_message=None):
        if reply_message:
            opponent_id = reply_message['from_id']
            if user_id == opponent_id:
                return 'Нельзя дуэлиться с самим собой!'
            pending_duels[opponent_id] = user_id
            user_name = get_user_name(user_id)
            return f'Пользователь {user_name} вызывает вас на дуэль! Ответьте "принять дуэль", чтобы начать.'
        else:
            return 'Ответьте на сообщение пользователя, чтобы вызвать его на дуэль.'

    @staticmethod
    def handle_accept_duel(user_id):
        if user_id in pending_duels:
            opponent_id = pending_duels[user_id]
            duel = DuelController(opponent_id, user_id)
            duels[user_id] = duel
            duels[opponent_id] = duel
            del pending_duels[user_id]
            user_name = get_user_name(user_id)
            opponent_name = get_user_name(opponent_id)
            return f'Дуэль началась! {opponent_name} против {user_name}. Первый ход за {opponent_name}.'
        else:
            return 'Вас никто не вызывал на дуэль.'

    @staticmethod
    def handle_shoot_command(user_id):
        if user_id not in duels:
            return 'Вы не участвуете в дуэли.'
        duel = duels[user_id]
        if duel.get_current_player() != user_id:
            return 'Сейчас не ваш ход.'
        hit, winner = duel.shoot()
        if winner:
            del duels[duel.players[0]]
            del duels[duel.players[1]]
            winner_name = get_user_name(winner)
            return f'Попадание!💥 Победитель: {winner_name}.'
        else:
            next_player_name = get_user_name(duel.get_current_player())
            return f'Промах!❌ Ход переходит к {next_player_name}.'

duels = {}
pending_duels = {}
