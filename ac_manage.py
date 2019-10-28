from copy import deepcopy
import json
import logging
from time import time
import traceback

from constants import MONITOR_ID


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

        logging.info('users: ' + str(self.users.keys()))
        logging.info('pairs: ' + str(self.pairs))
        for key, value in self.queue.items():
            logging.info(key + ': ' + str(value))

    def create_user(self, user_id, username, gender, preference):
        try:
            self.db_conn.store_user(user_id, username, gender, preference)
        except:
            self.bot.send_message(MONITOR_ID, 'Creation user exception:\n' + traceback.format_exc())
            logging.error('Creation user exception', exc_info=True)
            return

        self.users[user_id] = User(user_id, gender, preference)
        logging.warning('User {user} is created'.format(user=user_id))
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
                else:
                    setattr(user, key, updated_data[key])

        if updated_data:
            logging.warning('User {user} is updated: {data}'.format(user=user_id, data=str(updated_data)))
            try:
                self.db_conn.update_user(user_id, updated_data)
            except:
                self.bot.send_message(MONITOR_ID, 'Update user exception:\n' + traceback.format_exc())
                logging.error('Update user exception', exc_info=True)

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

        try:
            user = self.db_conn.load_user_by_id(user_id)
        except:
            self.bot.send_message(MONITOR_ID, 'Loading user exception:\n' + traceback.format_exc())
            logging.error('Loading user exception', exc_info=True)
            return

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

    def save_message(self, user1, user2, content, kind):
        try:
            self.db_conn.store_message(user1, user2, content, kind)
        except:
            self.bot.send_message(MONITOR_ID, 'Message store exception:\n' + traceback.format_exc())
            logging.error('Message store exception', exc_info=True)

    def close_chat(self, user1, user2):
        self.pairs.pop(user1)
        self.pairs.pop(user2)

        self.update_user(user1, {'partner': None})
        self.update_user(user2, {'partner': None})

        logging.warning('Chat is finished: {user1} {user2}'.format(user1=user1, user2=user2))

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
