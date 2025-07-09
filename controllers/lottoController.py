import random
import time
from controllers.messageController import get_user_name

class LottoController:
    def __init__(self):
        self.games = {}  # {peer_id: {host_id: id, players: {user_id: card}, drawn_numbers: [], current_game: bool}}
        self.pending_games = {}  # {peer_id: {host_id: id, players: [], timestamp: float}}

    def start_game(self, peer_id, host_id):
        """Создание лобби для игры в лото"""
        if peer_id in self.games:
            return "Игра в лото уже идет в этой беседе!"
        
        if peer_id in self.pending_games:
            return "Набор игроков уже идет! Напишите 'лото вступить', чтобы присоединиться."
        
        self.pending_games[peer_id] = {
            "host_id": host_id,
            "players": [host_id],
            "timestamp": time.time()
        }
        
        host_name = get_user_name(host_id)
        return f"🎲 {host_name} начинает набор игроков в лото!\n\n" \
               f"📝 Для участия напишите 'лото вступить'\n" \
               f"🎯 Для начала игры ведущий должен написать 'лото начать'\n" \
               f"⏰ У вас есть 5 минут для набора игроков"

    def join_game(self, peer_id, user_id):
        """Присоединение к лобби игры"""
        if peer_id not in self.pending_games:
            return "❌ Сейчас нет активного набора в лото."
        
        # Проверяем, не истекло ли время
        if time.time() - self.pending_games[peer_id]["timestamp"] > 300:  # 5 минут
            del self.pending_games[peer_id]
            return "⏰ Время набора игроков истекло."

        if user_id in self.pending_games[peer_id]["players"]:
            return "✅ Вы уже присоединились к игре."

        self.pending_games[peer_id]["players"].append(user_id)
        players_list = [get_user_name(pid) for pid in self.pending_games[peer_id]["players"]]
        
        return f"🎉 {get_user_name(user_id)} присоединился к игре в лото!\n\n" \
               f"👥 Текущие игроки ({len(players_list)}): {', '.join(players_list)}\n" \
               f"🎯 Ведущий может написать 'лото начать' для начала игры"

    def start_lotto(self, peer_id, user_id):
        """Запуск игры в лото (только ведущий может запустить)"""
        if peer_id not in self.pending_games:
            return "❌ Нет активного лобби для начала игры."
            
        if self.pending_games[peer_id]["host_id"] != user_id:
            host_name = get_user_name(self.pending_games[peer_id]["host_id"])
            return f"❌ Только ведущий ({host_name}) может начать игру!"
            
        if len(self.pending_games[peer_id]["players"]) < 2:
            return "❌ Нужно минимум 2 игрока для начала игры в лото."

        # Создаем карточки для игроков
        players = self.pending_games[peer_id]["players"]
        player_cards = {}
        
        for player_id in players:
            player_cards[player_id] = self._generate_lotto_card()
        
        # Создаем игру
        self.games[peer_id] = {
            "host_id": self.pending_games[peer_id]["host_id"],
            "players": player_cards,
            "drawn_numbers": [],
            "current_game": True,
            "numbers_left": list(range(1, 91))  # Числа от 1 до 90
        }
        
        # Удаляем лобби
        del self.pending_games[peer_id]
        
        # Формируем сообщение с карточками игроков
        response = "🎲 ИГРА В ЛОТО НАЧАЛАСЬ! 🎲\n\n"
        
        for player_id, card in player_cards.items():
            player_name = get_user_name(player_id)
            response += f"📋 Карточка {player_name}:\n"
            response += self._format_card(card) + "\n\n"
        
        response += "🎯 Ведущий может написать 'лото число', чтобы вытянуть следующий номер!\n"
        response += "✅ Игроки отмечают числа на своих карточках"
        
        return response

    def draw_number(self, peer_id, user_id):
        """Вытягивание следующего числа (только ведущий)"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if not self.games[peer_id]["current_game"]:
            return "❌ Игра в лото уже завершена."
            
        if self.games[peer_id]["host_id"] != user_id:
            host_name = get_user_name(self.games[peer_id]["host_id"])
            return f"❌ Только ведущий ({host_name}) может вытягивать числа!"
        
        if not self.games[peer_id]["numbers_left"]:
            return "🎉 Все числа уже вытянуты!"
        
        # Вытягиваем случайное число
        drawn_number = random.choice(self.games[peer_id]["numbers_left"])
        self.games[peer_id]["numbers_left"].remove(drawn_number)
        self.games[peer_id]["drawn_numbers"].append(drawn_number)
        
        response = f"🎲 Выпало число: {drawn_number}\n\n"
        response += f"📊 Вытянуто чисел: {len(self.games[peer_id]['drawn_numbers'])}/90\n"
        
        # Проверяем, есть ли у кого-то бинго
        winners = self._check_for_winners(peer_id)
        if winners:
            response += "\n🎉 БИНГО! 🎉\n"
            for winner_id in winners:
                winner_name = get_user_name(winner_id)
                response += f"🏆 Поздравляем {winner_name}!\n"
            
            self.games[peer_id]["current_game"] = False
            response += "\n🎮 Игра завершена!"
        else:
            response += "\n🎯 Ведущий может написать 'лото число' для следующего числа"
        
        return response

    def check_card(self, peer_id, user_id):
        """Показать карточку игрока с отмеченными числами"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if user_id not in self.games[peer_id]["players"]:
            return "❌ Вы не участвуете в этой игре."
        
        card = self.games[peer_id]["players"][user_id]
        drawn_numbers = self.games[peer_id]["drawn_numbers"]
        
        response = f"📋 Ваша карточка:\n"
        response += self._format_card_with_marks(card, drawn_numbers)
        
        # Проверяем, сколько чисел отмечено
        marked_count = sum(1 for row in card for num in row if num in drawn_numbers)
        total_count = sum(1 for row in card for num in row if num != 0)
        
        response += f"\n✅ Отмечено: {marked_count}/{total_count}"
        
        return response

    def get_drawn_numbers(self, peer_id):
        """Показать все вытянутые числа"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
        
        drawn = self.games[peer_id]["drawn_numbers"]
        if not drawn:
            return "🎲 Числа еще не вытягивались."
        
        response = f"🎯 Вытянутые числа ({len(drawn)}):\n"
        # Группируем числа по строкам для удобства
        response += " ".join(str(num) for num in drawn)
        
        return response

    def end_game(self, peer_id, user_id):
        """Завершение игры (только ведущий)"""
        if peer_id not in self.games:
            return "❌ Игра в лото не активна."
            
        if self.games[peer_id]["host_id"] != user_id:
            host_name = get_user_name(self.games[peer_id]["host_id"])
            return f"❌ Только ведущий ({host_name}) может завершить игру!"
        
        del self.games[peer_id]
        return "🎮 Игра в лото завершена ведущим."

    def _generate_lotto_card(self):
        """Генерация карточки лото 3x9 с числами от 1 до 90"""
        card = [[0 for _ in range(9)] for _ in range(3)]
        
        # Для каждого столбца определяем диапазон чисел
        for col in range(9):
            if col == 0:
                numbers = list(range(1, 10))
            elif col == 8:
                numbers = list(range(81, 91))
            else:
                numbers = list(range(col * 10, (col + 1) * 10))
            
            # Выбираем случайные числа для этого столбца
            selected = random.sample(numbers, 3)
            selected.sort()
            
            for row in range(3):
                card[row][col] = selected[row]
        
        # Заменяем некоторые числа на пустые места (0)
        for row in range(3):
            # В каждой строке должно быть 5 чисел и 4 пустых места
            positions_to_clear = random.sample(range(9), 4)
            for pos in positions_to_clear:
                card[row][pos] = 0
        
        return card

    def _format_card(self, card):
        """Форматирование карточки: только числа, по 5 в ряду, без разделителей"""
        result = ""
        for row in card:
            nums = [str(num).center(3) if num != 0 else "   " for num in row]
            # Оставляем только 5 чисел, остальные пустые
            filtered = [n for n in nums if n.strip()]
            while len(filtered) < 5:
                filtered.append("   ")
            result += " ".join(filtered) + "\n"
        return result

    def _format_card_with_marks(self, card, drawn_numbers):
        """Форматирование карточки с отметками: только числа, по 5 в ряду, без разделителей"""
        result = ""
        for row in card:
            nums = []
            for num in row:
                if num == 0:
                    continue
                elif num in drawn_numbers:
                    mark = f"✓{num}" if num >= 10 else f"✓{num}"
                    nums.append(mark.center(3))
                else:
                    nums.append(str(num).center(3))
            while len(nums) < 5:
                nums.append("   ")
            result += " ".join(nums) + "\n"
        return result

    def _check_for_winners(self, peer_id):
        """Проверка на победителей (полная карточка)"""
        winners = []
        drawn_numbers = set(self.games[peer_id]["drawn_numbers"])
        
        for player_id, card in self.games[peer_id]["players"].items():
            # Собираем все числа карточки (кроме пустых мест)
            player_numbers = set()
            for row in card:
                for num in row:
                    if num != 0:
                        player_numbers.add(num)
            
            # Проверяем, все ли числа игрока вытянуты
            if player_numbers.issubset(drawn_numbers):
                winners.append(player_id)
        
        return winners
