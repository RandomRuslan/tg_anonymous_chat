# -*- coding: utf-8 -*-
import telebot
from time import time

from constants import TOKEN


class Manager:
    users = None
    pairs = None
    queue = None

    def __init__(self):
        self.users = {}
        self.pairs = {}
        self.queue = set()


bot = telebot.TeleBot(TOKEN)
manager = Manager()


@bot.message_handler(commands=['start'])
def command_start(message):
    text = 'Добро пожаловать!\nПеред использованием бота обязательно прочтите инструкцию и предостережения, вызвав комманду /help'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['help'])
def command_help(message):
    text = 'Тыры-пыры'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['create'])
def command_create(message):
    sender_id = message.chat.id
    if manager.users.get(sender_id) is not None:
        bot.send_message(sender_id, 'Пользователь уже создан')
        return

    manager.users[sender_id] = {
        'is_male': True
    }
    print(manager.users)
    

@bot.message_handler(commands=['new'])
def command_new(message):
    sender_id = message.chat.id
    if manager.pairs.get(sender_id) is not None:
        bot.send_message(sender_id, 'Вы уже в диалоге!')
        return

    queue = manager.queue
    for id in queue:
        bot.send_message(sender_id, 'Пара найдена! Вы общаетесь с {}'.format(id))
        bot.send_message(id, 'Пара найдена! Вы общаетесь с {}'.format(sender_id))
        manager.queue.remove(id)
        manager.pairs[id] = sender_id
        manager.pairs[sender_id] = id
        break
    else:
        bot.send_message(sender_id, 'Ожидайте')
        print('User {} is waiting'.format(sender_id))
        manager.queue.add(sender_id)


@bot.message_handler(commands=['stop'])
def command_stop(message):
    sender_id = message.chat.id
    if sender_id in manager.queue:
        manager.queue.remove(sender_id)
        bot.send_message(sender_id, 'Поиск пары остановлен')
        return

    if manager.pairs.get(sender_id) is None:
        bot.send_message(sender_id, 'Начните диалог коммандой /new')
        return

    receiver_id = manager.pairs.pop(sender_id)
    manager.pairs.pop(receiver_id)

    bot.send_message(sender_id, 'Диалог окончен. Для начала нового диалога используйте команду /new')
    bot.send_message(receiver_id, 'Ваш собеседник прервал диалог. Для начала нового диалога используйте команду /new')


@bot.message_handler(content_types=["text"])
def main(message):
    sender_id = message.chat.id
    if manager.pairs.get(sender_id) is None:
        if sender_id in manager.queue:
            bot.send_message(sender_id, 'Все еще ожидайте')
            return
        else:
            bot.send_message(sender_id, 'Начните диалог коммандой /new')
            return

    receiver_id = manager.pairs[sender_id]
    bot.send_message(receiver_id, message.text)


if __name__ == '__main__':
    print("START")
    bot.polling(none_stop=True)
