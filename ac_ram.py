class Manager:

    def __init__(self, db_conn):
        self.db_conn = db_conn
        self.users = self.load_users()
        self.pairs = self.load_pairs()
        self.queue = set()

    def create_user(self, id, username, gender, preference):
        self.db_conn.create_user(id, username, gender, preference)
        self.users[id] = User(gender, preference)

    def load_users(self):
        users = {}
        for user in self.db_conn.load_users():
            users[user['id']] = User(user['gender'], user['preference'])

        return users

    def load_pairs(self):
        pairs = {}
        for pair in self.db_conn.load_pairs():
            if pair[0] not in pairs and pair[1] not in pairs:
                pairs[pair[0]] = pair[1]
                pairs[pair[1]] = pair[0]

        return pairs


class User:

    def __init__(self, gender, preference):
        self.gender = gender
        self.preference = preference
        self.current_chat = None
        self.last_chats = []

