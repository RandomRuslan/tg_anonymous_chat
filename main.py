# -*- coding: utf-8 -*-

import logging
from telebot import TeleBot, types
from time import time

from ac_db import DBConnecter
from ac_manage import Manager
from ac_monitor import on_error
from ac_repeater import Matcher, Cleaner
from ac_resources import Definitions
from constants import LOG_FILE, LOG_LEVEL, SUPPORT_EMAIL, TOKEN

bot = TeleBot(TOKEN)


def show_gender_keyboard(sender_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton(definitions.get_text('button.f')),
        types.KeyboardButton(definitions.get_text('button.m'))
    )

    bot.send_message(sender_id, definitions.get_text('info.choose_gender'), reply_markup=markup)


def try_to_create_user(message):
    sender_id = message.chat.id
    text = message.text or ''
    text = text.strip().lower()

    if not text:
        bot.send_message(sender_id, definitions.get_text('refuse.lack.user'))
        show_gender_keyboard(sender_id)
        return

    if text in ['м', 'm', definitions.get_text('button.m').strip().lower()]:
        gender = 'm'
        preference = 'f'
    elif text in ['ж', 'f', definitions.get_text('button.f').strip().lower()]:
        gender = 'f'
        preference = 'm'
    else:
        show_gender_keyboard(sender_id)
        return

    manager.create_user(sender_id, message.chat.username, gender, preference)

    markup = types.ReplyKeyboardRemove(selective=False)
    text = definitions.get_text('accept.done.user', gender=gender, preference=preference)
    bot.send_message(sender_id, text, reply_markup=markup)
    bot.send_message(sender_id, definitions.get_text('info.choose_preference'))


def check_user(func):
    def wrapper(message):
        sender_id = message.chat.id
        user = manager.get_user_by_id(sender_id)
        if not user:
            try_to_create_user(message)
            return

        user.last_activity_ts = int(time())
        try:
            func(message)
        except:
            on_error(manager.bot, 'Command exception')

    return wrapper


@bot.message_handler(commands=['start'])
def command_start(message):
    bot.send_message(message.chat.id, definitions.get_text('info.welcome'))
    bot.send_message(message.chat.id, definitions.get_text('info.commands'))
    bot.send_message(message.chat.id, definitions.get_text('info.feedback', SUPPORT_EMAIL))
    show_gender_keyboard(message.chat.id)


@bot.message_handler(commands=['help'])
def command_help(message):
    bot.send_message(message.chat.id, definitions.get_text('info.helper'))
    bot.send_message(message.chat.id, definitions.get_text('info.commands'))
    bot.send_message(message.chat.id, definitions.get_text('info.feedback', SUPPORT_EMAIL))


@bot.message_handler(commands=['prefer'])
@check_user
def command_prefer(message):
    sender_id = message.chat.id

    user = manager.users[sender_id]
    if user.partner is not None:
        bot.send_message(sender_id, definitions.get_text('refuse.preference_during_processing'))
        return

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

    manager.update_user(sender_id, {'preference': preference})
    bot.send_message(sender_id, definitions.get_text('accept.done.preference', preference=preference))


@bot.message_handler(commands=['new'])
@check_user
def command_new(message):
    sender_id = message.chat.id
    user = manager.users[sender_id]

    if user.partner:
        bot.send_message(sender_id, definitions.get_text('refuse.already.chat'))
        return

    if user.partner == 0:
        bot.send_message(sender_id, definitions.get_text('refuse.already.search'))
        return

    bot.send_message(sender_id, definitions.get_text('accept.start.search'))
    manager.queue[user.queue_key].append(sender_id)
    manager.update_user(sender_id, {'partner': 0})


@bot.message_handler(commands=['stop'])
@check_user
def command_stop(message):
    sender_id = message.chat.id
    user = manager.users[sender_id]

    if user.partner == 0:
        manager.queue[user.queue_key].remove(sender_id)
        manager.update_user(sender_id, {'partner': None})
        bot.send_message(sender_id, definitions.get_text('accept.stop.search'))
        return

    if user.partner is None:
        bot.send_message(sender_id, definitions.get_text('info.command_new'))
        return

    receiver_id = manager.pairs[sender_id]

    bot.send_message(sender_id, definitions.get_text('accept.stop.chat'))
    bot.send_message(receiver_id, definitions.get_text('abrupt.chat_is_interrupted'))

    manager.close_chat(sender_id, receiver_id)


def handle_message(func):
    def wrapper(message):
        sender_id = message.chat.id
        user = manager.get_user_by_id(sender_id)
        if not user:
            try_to_create_user(message)
            return

        if user.partner == 0:
            bot.send_message(sender_id, definitions.get_text('refuse.already.search'))
            return

        if user.partner is None:
            bot.send_message(sender_id, definitions.get_text('info.command_new'))
            return

        receiver_id = manager.pairs[sender_id]

        try:
            content = func(message, sender_id, receiver_id)
        except:
            on_error(manager.bot, 'Message exception')
            return

        if message.caption:
            bot.send_message(receiver_id, message.caption)
            manager.save_message(sender_id, receiver_id, message.caption, 'text')

        manager.save_message(sender_id, receiver_id, str(content), message.content_type)

    return wrapper


@bot.message_handler(content_types=['text'])
@handle_message
def on_message_text(message, sender_id, receiver_id):
    content = message.text
    bot.send_message(receiver_id, content)

    return content


@bot.message_handler(content_types=['voice'])
@handle_message
def on_message_voice(message, sender_id, receiver_id):
    content = message.voice.file_id
    bot.send_voice(receiver_id, content)

    return content


@bot.message_handler(content_types=['sticker'])
@handle_message
def on_message_sticker(message, sender_id, receiver_id):
    content = message.sticker.file_id
    bot.send_sticker(receiver_id, content)

    return content


@bot.message_handler(content_types=['audio'])
@handle_message
def on_message_audio(message, sender_id, receiver_id):
    content = message.audio.file_id
    bot.send_audio(receiver_id, content)

    return content


@bot.message_handler(content_types=['photo'])
@handle_message
def on_message_photo(message, sender_id, receiver_id):
    content = message.photo[-1].file_id
    bot.send_photo(receiver_id, content)

    return content


@bot.message_handler(content_types=['video'])
@handle_message
def on_message_video(message, sender_id, receiver_id):
    content = message.video.file_id
    bot.send_video(receiver_id, content)

    return content


@bot.message_handler(content_types=['video_note'])
@handle_message
def on_message_video_note(message, sender_id, receiver_id):
    content = message.video_note.file_id
    bot.send_video_note(receiver_id, content)

    return content


@bot.message_handler(content_types=['document'])
@handle_message
def on_message_document(message, sender_id, receiver_id):
    content = message.document.file_id
    bot.send_document(receiver_id, content)

    return content


if __name__ == '__main__':
    print('START')
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        format=u'%(levelname)s [%(asctime)s %(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y%m%d %H:%M:%S'
    )
    logging.warning('START')

    db_conn = DBConnecter()
    manager = Manager(db_conn, bot)

    definitions = Definitions()
    matcher = Matcher(manager)
    cleaner = Cleaner(manager, bot)

    bot.polling(none_stop=True)
