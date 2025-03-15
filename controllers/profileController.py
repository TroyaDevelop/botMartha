import json
import os

class ProfileController:
    def __init__(self):
        self.profiles = self.load_profiles()

    def load_profiles(self):
        if not os.path.exists('data/profiles.json'):
            with open('data/profiles.json', 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
        with open('data/profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_profiles(self):
        with open('data/profiles.json', 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, ensure_ascii=False, indent=4)

    def set_nickname(self, user_id, nickname):
        if str(user_id) not in self.profiles:
            self.profiles[str(user_id)] = {}
        self.profiles[str(user_id)]['nickname'] = nickname
        self.save_profiles()

    def get_nickname(self, user_id):
        return self.profiles.get(str(user_id), {}).get('nickname')

    def get_profile(self, user_id):
        profiles = self.load_profiles()
        profile = profiles.get(str(user_id), {})
        if profile:
            nickname = profile.get('nickname', 'Не указан')
            duel_wins = profile.get('duel_wins', 0)
            return f"Ваш профиль:\nНикнейм: {nickname}\nУбийств в дуэлях: {duel_wins}"
        return "Ваш профиль пока пуст."
