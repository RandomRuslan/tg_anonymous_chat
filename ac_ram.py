import random
from threading import Timer


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

        Repeater(5, self.match_pairs).start()

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

    def load_pairs(self):
        pairs = {}
        for pair in self.db_conn.load_pairs():
            if pair[0] not in pairs and pair[1] not in pairs:
                pairs[pair[0]] = pair[1]
                pairs[pair[1]] = pair[0]

        return pairs

    def match_pairs(self):
        print('match')

        processed_queue = list(self.queue['ff'])
        for user_id in processed_queue:
            if user_id in self.queue['ff']:
                self._do_match(user_id, self.queue['ff'], [self.queue['ff'], self.queue['fb']])

        processed_queue = list(self.queue['mm'])
        for user_id in processed_queue:
            if user_id in self.queue['mm']:
                self._do_match(user_id, self.queue['mm'], [self.queue['mm'], self.queue['mb']])

        processed_queue = list(self.queue['fm'])
        for user_id in processed_queue:
            if user_id in self.queue['fm']:
                self._do_match(user_id, self.queue['fm'], [self.queue['mf'], self.queue['mb']])

        processed_queue = list(self.queue['mf'])
        for user_id in processed_queue:
            if user_id in self.queue['mf']:
                self._do_match(user_id, self.queue['mf'], [self.queue['fb']])

        processed_queue = list(self.queue['fb'])
        for user_id in processed_queue:
            if user_id in self.queue['fb']:
                self._do_match(user_id, self.queue['fb'], [self.queue['fb'], self.queue['mb']])

        processed_queue = list(self.queue['mb'])
        for user_id in processed_queue:
            if user_id in self.queue['mb']:
                self._do_match(user_id, self.queue['mb'], [self.queue['mb']])

    def _do_match(self, user_id, processed_queue, queues):
        user_list_for_choice = set()
        for queue in queues:
            user_list_for_choice.update(set(queue))

        while user_list_for_choice:
            random_user_id = random.sample(user_list_for_choice, 1)[0]
            if random_user_id != user_id:
                if user_id not in self.users[random_user_id].last_chats and \
                        random_user_id not in self.users[user_id].last_chats:

                    self.pairs[user_id] = random_user_id
                    self.pairs[random_user_id] = user_id

                    self.users[user_id].last_chats.append(random_user_id)
                    self.users[random_user_id].last_chats.append(user_id)
                    if len(self.users[user_id].last_chats) > User.MAX_LAST_CHATS:
                        self.users[user_id].last_chats.pop(0)
                    if len(self.users[random_user_id].last_chats) > User.MAX_LAST_CHATS:
                        self.users[random_user_id].last_chats.pop(0)

                    processed_queue.remove(user_id)
                    for queue in queues:
                        if random_user_id in queue:
                            queue.remove(random_user_id)
                            break

                    self.bot.send_message(user_id, 'Пара найдена. Ваш партнер: ' + str(random_user_id))
                    self.bot.send_message(random_user_id, 'Пара найдена. Ваш партнер: ' + str(user_id))

                    return

            user_list_for_choice.remove(random_user_id)


class User:

    MAX_LAST_CHATS = 5

    def __init__(self, gender, preference):
        self.gender = gender
        self.preference = preference
        self.queue_key = gender + preference
        self.last_chats = []


class Repeater:

    def __init__(self, period, repetitive_function):
        self.period = period
        self.repetitive_function = repetitive_function
        self.thread = Timer(self.period, self.handle_function)

    def handle_function(self):
        self.repetitive_function()
        self.thread = Timer(self.period, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()
