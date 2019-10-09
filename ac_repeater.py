import random
from time import time
from threading import Timer

from ac_manage import User


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


class Matcher:
    
    def __init__(self, manager):
        self.manager = manager
        Repeater(5, self.match_pairs).start()

    def match_pairs(self):
        print('match')

        processed_queue = list(self.manager.queue['ff'])
        for user_id in processed_queue:
            if user_id in self.manager.queue['ff']:
                self._do_match(user_id, self.manager.queue['ff'], [self.manager.queue['ff'], self.manager.queue['fb']])

        processed_queue = list(self.manager.queue['mm'])
        for user_id in processed_queue:
            if user_id in self.manager.queue['mm']:
                self._do_match(user_id, self.manager.queue['mm'], [self.manager.queue['mm'], self.manager.queue['mb']])

        processed_queue = list(self.manager.queue['fm'])
        for user_id in processed_queue:
            if user_id in self.manager.queue['fm']:
                self._do_match(user_id, self.manager.queue['fm'], [self.manager.queue['mf'], self.manager.queue['mb']])

        processed_queue = list(self.manager.queue['mf'])
        for user_id in processed_queue:
            if user_id in self.manager.queue['mf']:
                self._do_match(user_id, self.manager.queue['mf'], [self.manager.queue['fb']])

        processed_queue = list(self.manager.queue['fb'])
        for user_id in processed_queue:
            if user_id in self.manager.queue['fb']:
                self._do_match(user_id, self.manager.queue['fb'], [self.manager.queue['fb'], self.manager.queue['mb']])

        processed_queue = list(self.manager.queue['mb'])
        for user_id in processed_queue:
            if user_id in self.manager.queue['mb']:
                self._do_match(user_id, self.manager.queue['mb'], [self.manager.queue['mb']])

    def _do_match(self, user_id, processed_queue, queues):
        user_set_for_choice = set()
        for queue in queues:
            user_set_for_choice.update(set(queue))

        while user_set_for_choice:
            random_user_id = random.sample(user_set_for_choice, 1)[0]
            if random_user_id != user_id:
                if user_id not in self.manager.users[random_user_id].prev_chats and \
                        random_user_id not in self.manager.users[user_id].prev_chats:

                    self.manager.bot.send_message(user_id, 'Пара найдена. Ваш партнер: ' + str(random_user_id))
                    self.manager.bot.send_message(random_user_id, 'Пара найдена. Ваш партнер: ' + str(user_id))

                    self.manager.pairs[user_id] = random_user_id
                    self.manager.pairs[random_user_id] = user_id

                    self.manager.users[user_id].prev_chats.append(random_user_id)
                    self.manager.users[random_user_id].prev_chats.append(user_id)
                    if len(self.manager.users[user_id].prev_chats) > User.MAX_PREV_CHATS:
                        self.manager.users[user_id].prev_chats.pop(0)
                    if len(self.manager.users[random_user_id].prev_chats) > User.MAX_PREV_CHATS:
                        self.manager.users[random_user_id].prev_chats.pop(0)

                    processed_queue.remove(user_id)
                    for queue in queues:
                        if random_user_id in queue:
                            queue.remove(random_user_id)
                            break

                    self.manager.update_user(user_id, {
                        'prev_chats': self.manager.users[user_id].prev_chats,
                        'state': User.State.CHAT
                    })
                    self.manager.update_user(random_user_id, {
                        'prev_chats': self.manager.users[random_user_id].prev_chats,
                        'state': User.State.CHAT
                    })

                    return

            user_set_for_choice.remove(random_user_id)


class Cleaner:

    ALLOWED_INACTIVITY_PERIOD = 60 * 60

    def __init__(self, manager, bot):
        self.manager = manager
        self.bot = bot

        Repeater(30 * 60, self.clean_inactive_users).start()

    def clean_inactive_users(self):
        print('clean users')
        print('Users before:', self.manager.users.keys())

        now = int(time())
        users = list(self.manager.users)
        for user_id in users:
            user = self.manager.users[user_id]
            if user.state != User.State.CHAT and now - user.last_activity_ts > self.ALLOWED_INACTIVITY_PERIOD:
                if user.state == User.State.CHAT:
                    text = 'К сожалению, поиск прерван. Для возобновления поиска используйте команду /new'
                    self.bot.send_message(user_id, text)
                    self.manager.queue[user.queue_key].remove(user_id)
                    self.manager.update_user(user_id, {'state': None})

                del self.manager.users[user_id]

        print('Users after:', self.manager.users.keys())
