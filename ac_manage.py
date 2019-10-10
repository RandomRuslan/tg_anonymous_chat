import json
from time import time
from copy import deepcopy


class Manager:

    def __init__(self, db_conn, bot):
        self.db_conn = db_conn
        self.bot = bot

        self.users = self.load_users()

        self.pairs = {}
        self.queue = {
            'mm': [], 'mf': [], 'mb': [],
            'ff': [], 'fm': [], 'fb': []
        }
        self.arrange_users()

        print(self.users.keys())
        print(self.pairs)
        for q in self.queue.values():
            print(q)

    def create_user(self, user_id, username, gender, preference):
        self.db_conn.create_user(user_id, username, gender, preference)
        self.users[user_id] = User(user_id, gender, preference)
        return self.users[user_id]

    def update_user(self, user_id, updated_data):
        user = self.users.get(user_id)
        if not user:
            return

        for key in deepcopy(updated_data):
            if getattr(user, key) == updated_data[key]:
                del updated_data[key]
            else:
                if key == 'prev_partners':
                    if len(updated_data[key]) > User.MAX_PREV_CHATS:
                        updated_data[key].pop(0)
                    setattr(user, key, updated_data[key])
                    updated_data[key] = json.dumps(updated_data[key]) if updated_data[key] else None

        if updated_data:
            self.db_conn.update_user(user_id, updated_data)

    def load_users(self):
        users = {}
        for user in self.db_conn.load_users():
            users[user['id']] = User(
                user['id'],
                user['gender'],
                user['preference'],
                prev_partners=user['prev_partners'],
                partner=user['partner']
            )

        return users

    def get_user_by_id(self, user_id):
        if self.users.get(user_id):
            return self.users[user_id]

        user = self.db_conn.load_user_by_id(user_id)
        if user:
            self.users[user_id] = User(
                user['id'],
                user['gender'],
                user['preference'],
                prev_partners=user['prev_partners'],
                partner=user['partner']
            )
            return self.users[user_id]

    def arrange_users(self):
        for user in self.users.values():
            if user.partner == 0:
                self.queue[user.queue_key].append(user.id)
            elif user.partner:
                self.pairs[user.id] = user.partner

    def close_chat(self, userid1, userid2):
        self.pairs.pop(userid1)
        self.pairs.pop(userid2)

        self.update_user(userid1, {'partner': None})
        self.update_user(userid2, {'partner': None})

        # self.db_conn.close_chat(userid1, userid2)


class User:

    MAX_PREV_CHATS = 5

    def __init__(self, id, gender, preference, prev_partners=None, partner=None):
        self.id = id
        self.gender = gender
        self.preference = preference
        self.queue_key = gender + preference
        self.prev_partners = prev_partners or []
        self.last_activity_ts = int(time())
        self.partner = partner
