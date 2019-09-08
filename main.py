# -*- coding: utf-8 -*-
import telebot
from time import time

from constants import TOKEN
from ac_db import DBConnecter


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
    text = 'Тыры-пыры helper'
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['create'])
def command_create(message):
    sender_id = message.chat.id
    if manager.users.get(sender_id) is not None:
        bot.send_message(sender_id, 'Пользователь уже создан')
        return

    text = message.text.split()
    if len(text) < 2:
        bot.send_message(sender_id, 'Необходимо указать ваш пол')
        return

    gender = text[1]
    if gender.lower() in ['м', 'm']:
        gender = 'm'
    elif gender.lower() in ['ж', 'f']:
        gender = 'f'
    else:
        bot.send_message(sender_id, 'Пол указан неверно')
        return

    if len(text) > 2:
        preference = text[2]
        if preference in ['м', 'm']:
            preference = 'm'
        elif preference in ['ж', 'f']:
            preference = 'f'
        else:
            preference = 'b'
    else:
        preference = 'b'

    db_conn.create_user(sender_id, message.chat.username, gender, preference)

    manager.users[sender_id] = {
        'gender': gender,
        'preference': preference
    }

    bot.send_message(sender_id, 'Создан пользователь:\nпол - {gender}\nпредпочтения - {preference}'
                     .format(gender=gender, preference=preference))


@bot.message_handler(commands=['new'])
def command_new(message):
    sender_id = message.chat.id
    if manager.pairs.get(sender_id) is not None:
        bot.send_message(sender_id, 'Вы уже в диалоге!')
        return

    queue = manager.queue
    if sender_id in queue:
        bot.send_message(sender_id, 'Поиск уже идет')
        return

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


def check_partner(func):
    def wrapper(message):
        sender_id = message.chat.id
        if manager.pairs.get(sender_id) is None:
            if sender_id in manager.queue:
                bot.send_message(sender_id, 'Все еще ожидайте')
                return
            else:
                bot.send_message(sender_id, 'Начните диалог коммандой /new')
                return

        receiver_id = manager.pairs[sender_id]

        func(message, sender_id, receiver_id)

        if message.caption:
            bot.send_message(receiver_id, message.caption)

    return wrapper


@bot.message_handler(content_types=['text'])
@check_partner
def on_message_text(message, sender_id, receiver_id):
    bot.send_message(receiver_id, message.text)


@bot.message_handler(content_types=['voice'])
@check_partner
def on_message_voice(message, sender_id, receiver_id):
    bot.send_voice(receiver_id, message.voice.file_id)


@bot.message_handler(content_types=['sticker'])
@check_partner
def on_message_sticker(message, sender_id, receiver_id):
    bot.send_sticker(receiver_id, message.sticker.file_id)


@bot.message_handler(content_types=['audio'])
@check_partner
def on_message_audio(message, sender_id, receiver_id):
    bot.send_audio(receiver_id, message.audio.file_id)


@bot.message_handler(content_types=['photo'])
@check_partner
def on_message_photo(message, sender_id, receiver_id):
    bot.send_photo(receiver_id, message.photo[-1].file_id)


@bot.message_handler(content_types=['video'])
@check_partner
def on_message_video(message, sender_id, receiver_id):
    bot.send_video(receiver_id, message.video.file_id)


@bot.message_handler(content_types=['video_note'])
@check_partner
def on_message_video_note(message, sender_id, receiver_id):
    bot.send_video_note(receiver_id, message.video_note.file_id)


@bot.message_handler(content_types=['document'])
@check_partner
def on_message_document(message, sender_id, receiver_id):
    bot.send_document(receiver_id, message.document.file_id)


if __name__ == '__main__':
    print("START")
    db_conn = DBConnecter()
    bot.polling(none_stop=True)
