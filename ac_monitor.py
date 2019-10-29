import logging
import traceback

from constants import MONITOR_ID


def on_error(bot, message):
    text = message + ':\n' + '\n'.join(traceback.format_exc().splitlines()[-3:])
    bot.send_message(MONITOR_ID, text)
    logging.error(message, exc_info=True)
