import json
from time import time
from copy import deepcopy


class Manager:

    def __init__(self, db_conn, bot):
        self.db_conn = db_conn
        self.bot = bot

        self.users = self.load_users()
        self.pairs = self.load_pairs()

        self.queue = {
            'mm': [],
            'mf': [],
            'mb': [],
            'ff': [],
            'fm': [],
            'fb': []
        }
        self.fill_queue()

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
                setattr(user, key, updated_data[key])

        if updated_data:
            self.db_conn.update_user(user_id, updated_data)

    def load_users(self):
        users = {}
        for user in self.db_conn.load_users():
            users[user['id']] = User(
                user['id'],
                user['gender'],
                user['preference'],
                prev_chats=user['prev_chats'],
                state=user['state']
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
                prev_chats=user['prev_chats'],
                state=user['state']
            )
            return self.users[user_id]

    def load_pairs(self):
        pairs = {}
        for pair in self.db_conn.load_pairs():
            if pair[0] not in pairs and pair[1] not in pairs:
                pairs[pair[0]] = pair[1]
                pairs[pair[1]] = pair[0]

        return pairs

    def fill_queue(self):
        for user in self.users.values():
            if user.state == User.State.QUEUE:
                self.queue[user.queue_key].append(user.id)

    def close_chat(self, userid1, userid2):
        self.pairs.pop(userid1)
        self.pairs.pop(userid2)

        self.update_user(userid1, {'state': None})
        self.update_user(userid2, {'state': None})

        self.db_conn.close_chat(userid1, userid2)


class User:

    MAX_PREV_CHATS = 5

    class State:
        QUEUE = 'queue'
        CHAT = 'chat'

    def __init__(self, id, gender, preference, prev_chats=None, state=None):
        self.id = id
        self.gender = gender
        self.preference = preference
        self.queue_key = gender + preference
        self.prev_chats = json.loads(prev_chats) if prev_chats else []
        self.last_activity_ts = int(time())
        self.state = state
