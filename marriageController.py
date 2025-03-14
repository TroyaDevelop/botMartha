import json
import time
from messageController import get_user_name

class MarriageController:
    def __init__(self):
        self.marriages = {}
        self.pending_proposals = {}
        self.pending_divorces = {}

    @staticmethod
    def load_marriages():
        try:
            with open('marriages.json', 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_marriages(marriages):
        with open('marriages.json', 'w', encoding='utf-8') as file:
            json.dump(marriages, file, ensure_ascii=False, indent=4)

    def propose_marriage(self, user_id, peer_id, reply_message=None):
        if reply_message:
            partner_id = reply_message['from_id']
            if user_id == partner_id:
                return 'Нельзя заключить брак с самим собой!'
            if str(partner_id) in self.marriages.get(str(peer_id), {}):
                return 'Этот пользователь уже состоит в браке.'
            self.pending_proposals[partner_id] = {'proposer': user_id, 'timestamp': time.time(), 'peer_id': peer_id}
            user_name = get_user_name(user_id)
            return f'Пользователь {user_name} предлагает вам заключить брак!💍 Ответьте "принять брак", чтобы согласиться.'
        else:
            return 'Ответьте на сообщение пользователя, чтобы предложить брак.'

    def accept_marriage(self, user_id):
        if user_id in self.pending_proposals:
            if time.time() - self.pending_proposals[user_id]['timestamp'] > 60:
                del self.pending_proposals[user_id]
                return 'Время на принятие предложения истекло.'
            proposer_id = self.pending_proposals[user_id]['proposer']
            peer_id = self.pending_proposals[user_id]['peer_id']
            
            sorted_ids = tuple(sorted([proposer_id, user_id]))
            if str(peer_id) not in self.marriages:
                self.marriages[str(peer_id)] = {}
            
            if str(sorted_ids) not in self.marriages[str(peer_id)]:
                self.marriages[str(peer_id)][str(sorted_ids)] = {'date': time.strftime('%d-%m-%Y')}
                self.save_marriages(self.marriages)
            
            del self.pending_proposals[user_id]
            return f'Поздравляем! {get_user_name(proposer_id)} и {get_user_name(user_id)} теперь состоят в браке.💍💖'
        else:
            return 'Вам никто не предлагал брак.'

    def divorce(self, user_id, peer_id):
        self.marriages = self.load_marriages()
        if str(peer_id) in self.marriages:
            for pair, data in self.marriages[str(peer_id)].items():
                if str(user_id) in pair:
                    self.pending_divorces[user_id] = {'peer_id': peer_id, 'timestamp': time.time()}
                    return 'Вы уверены, что хотите развестись?😢 Ответьте "подтвердить развод", чтобы завершить развод.'
        return 'Вы не состоите в браке.'

    def confirm_divorce(self, user_id):
        if user_id in self.pending_divorces:
            if time.time() - self.pending_divorces[user_id]['timestamp'] > 60:
                del self.pending_divorces[user_id]
                return 'Время на подтверждение развода истекло.'
            peer_id = self.pending_divorces[user_id]['peer_id']
            self.marriages = self.load_marriages()
            if str(peer_id) in self.marriages:
                for pair, data in self.marriages[str(peer_id)].items():
                    if str(user_id) in pair:
                        id1, id2 = eval(pair)
                        partner_id = id1 if str(user_id) == str(id2) else id2
                        del self.marriages[str(peer_id)][pair]
                        self.save_marriages(self.marriages)
                        del self.pending_divorces[user_id]
                        user_name = get_user_name(user_id)
                        partner_name = get_user_name(partner_id)
                        return f'{user_name} и {partner_name} больше не состоят в браке.😭💔'
            return 'Вы не состоите в браке.'
        else:
            return 'У вас нет ожидающего подтверждения развода.'

    def get_marriages(self, peer_id):
        self.marriages = self.load_marriages()
        return {k: v for k, v in self.marriages.get(str(peer_id), {}).items() if v}

marriage_controller = MarriageController()
