from time import time


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

    def create_user(self, user_id, username, gender, preference):
        self.db_conn.create_user(user_id, username, gender, preference)
        self.users[user_id] = User(gender, preference)
        return self.users[user_id]

    def update_user(self, user_id, preference):
        if self.users.get(user_id) and self.users[user_id].preference != preference:
            self.db_conn.update_user(user_id, preference)

    def load_users(self):
        users = {}
        for user in self.db_conn.load_users():
            users[user['id']] = User(user['gender'], user['preference'])

        return users

    def get_user_by_id(self, user_id):
        if self.users.get(user_id):
            return self.users[user_id]

        user = self.db_conn.load_user_by_id(user_id)
        if user:
            self.users[user_id] = User(user.gender, user.preference)
            return self.users[user_id]

    def load_pairs(self):
        pairs = {}
        for pair in self.db_conn.load_pairs():
            if pair[0] not in pairs and pair[1] not in pairs:
                pairs[pair[0]] = pair[1]
                pairs[pair[1]] = pair[0]

        return pairs


class User:

    MAX_LAST_CHATS = 5

    def __init__(self, gender, preference):
        self.gender = gender
        self.preference = preference
        self.queue_key = gender + preference
        self.last_chats = []
        self.last_activity_ts = int(time())
