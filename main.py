# -*- coding: utf-8 -*-
import telebot
from time import time

from constants import TOKEN
from ac_db import DBConnecter
from ac_ram import Manager
from ac_resources import Definitions

bot = telebot.TeleBot(TOKEN)


def check_user(func):
    def wrapper(message):
        sender_id = message.chat.id
        if manager.users.get(sender_id) is None:
            bot.send_message(sender_id, definitions.get_text('refuse.lack.user'))
            return

        func(message)

    return wrapper


@bot.message_handler(commands=['start'])
def command_start(message):
    text = definitions.get_text('info.welcome')
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['help'])
def command_help(message):
    text = definitions.get_text('info.helper')
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['create'])
def command_create(message):
    sender_id = message.chat.id
    if manager.users.get(sender_id) is not None:
        bot.send_message(sender_id, definitions.get_text('refuse.user_is_created'))
        return

    text = message.text.split()
    if len(text) < 2:
        bot.send_message(sender_id, definitions.get_text('refuse.lack.gender'))
        return

    gender = text[1]
    if gender.lower() in ['м', 'm']:
        gender = 'm'
    elif gender.lower() in ['ж', 'f']:
        gender = 'f'
    else:
        bot.send_message(sender_id, definitions.get_text('refuse.incorrect_gender'))
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

    manager.create_user(sender_id, message.chat.username, gender, preference)
    bot.send_message(sender_id, definitions.get_text('accept.done.user', gender=gender, preference=preference))


@bot.message_handler(commands=['prefer'])
@check_user
def command_prefer(message):
    sender_id = message.chat.id
    text = message.text.split()
    if len(text) < 2:
        bot.send_message(sender_id, definitions.get_text('refuse.lack.preference'))
        return

    preference = text[1]
    if preference in ['м', 'm']:
        preference = 'm'
    elif preference in ['ж', 'f']:
        preference = 'f'
    else:
        preference = 'b'

    manager.update_user(sender_id, preference)
    bot.send_message(sender_id, definitions.get_text('accept.done.preference', preference=preference))


@bot.message_handler(commands=['new'])
@check_user
def command_new(message):
    sender_id = message.chat.id
    user = manager.users[sender_id]

    if manager.pairs.get(sender_id) is not None:
        bot.send_message(sender_id, definitions.get_text('refuse.already.chat'))
        return

    if sender_id in manager.queue[user.queue_key]:
        bot.send_message(sender_id, definitions.get_text('refuse.already.search'))
        return

    bot.send_message(sender_id, definitions.get_text('accept.start.search'))
    manager.queue[user.queue_key].append(sender_id)


@bot.message_handler(commands=['stop'])
@check_user
def command_stop(message):
    sender_id = message.chat.id
    if sender_id in manager.queue:
        manager.queue.remove(sender_id)
        bot.send_message(sender_id, definitions.get_text('accept.stop.search'))
        return

    if manager.pairs.get(sender_id) is None:
        bot.send_message(sender_id, definitions.get_text('info.command_new'))
        return

    receiver_id = manager.pairs.pop(sender_id)
    manager.pairs.pop(receiver_id)

    bot.send_message(sender_id, definitions.get_text('accept.stop.chat'))
    bot.send_message(receiver_id, definitions.get_text('abrupt.chat_is_interrupted'))
    db_conn.close_chat(sender_id, receiver_id)


def handle_message(func):
    def wrapper(message):
        sender_id = message.chat.id
        if manager.pairs.get(sender_id) is None:
            if sender_id in manager.queue:
                bot.send_message(sender_id, definitions.get_text('refuse.already.search'))
                return
            else:
                bot.send_message(sender_id, definitions.get_text('info.command_new'))
                return

        receiver_id = manager.pairs[sender_id]

        func(message, sender_id, receiver_id)

        if message.caption:
            bot.send_message(receiver_id, message.caption)

    return wrapper


@bot.message_handler(content_types=['text'])
@handle_message
def on_message_text(message, sender_id, receiver_id):
    bot.send_message(receiver_id, message.text)


@bot.message_handler(content_types=['voice'])
@handle_message
def on_message_voice(message, sender_id, receiver_id):
    bot.send_voice(receiver_id, message.voice.file_id)


@bot.message_handler(content_types=['sticker'])
@handle_message
def on_message_sticker(message, sender_id, receiver_id):
    bot.send_sticker(receiver_id, message.sticker.file_id)


@bot.message_handler(content_types=['audio'])
@handle_message
def on_message_audio(message, sender_id, receiver_id):
    bot.send_audio(receiver_id, message.audio.file_id)


@bot.message_handler(content_types=['photo'])
@handle_message
def on_message_photo(message, sender_id, receiver_id):
    bot.send_photo(receiver_id, message.photo[-1].file_id)


@bot.message_handler(content_types=['video'])
@handle_message
def on_message_video(message, sender_id, receiver_id):
    bot.send_video(receiver_id, message.video.file_id)


@bot.message_handler(content_types=['video_note'])
@handle_message
def on_message_video_note(message, sender_id, receiver_id):
    bot.send_video_note(receiver_id, message.video_note.file_id)


@bot.message_handler(content_types=['document'])
@handle_message
def on_message_document(message, sender_id, receiver_id):
    bot.send_document(receiver_id, message.document.file_id)


if __name__ == '__main__':
    print('START')
    db_conn = DBConnecter()
    manager = Manager(db_conn, bot)
    definitions = Definitions()
    bot.polling(none_stop=True)
