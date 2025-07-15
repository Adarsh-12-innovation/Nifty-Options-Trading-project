import asyncio
import threading
import traceback

from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, Bot
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, InlineQueryHandler
from KiteAuto import get_link, get_otp, set_access_token
from global_strings import bot_token, group_chat_id, commands_active_time
from datetime import datetime, time, timedelta

bot = Bot(token=bot_token)
chat_id = group_chat_id
application_ = ApplicationBuilder().token(bot_token).build()
global_application_msg = ""


async def end_application(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=chat_id, text='Commands Disabled after scheduled time')
    application_.stop_running()


async def send_msg(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=chat_id, text=global_application_msg)


async def enable_command_msg(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=chat_id, text='Enabling the commands now for '+str(commands_active_time)+' minutes')


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=chat_id, text="Commands Disabled")
    application_.stop_running()


def send_telegram_message(text_=""):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_telegram_message_core(text_))
    except Exception as e:
        print("Got the error below while sending telegram message\n"+e.__str__())
        print(traceback.format_exc())


async def send_telegram_message_core(text_=""):
    # Send a message to the private group
    await bot.send_message(chat_id=chat_id, text=text_)


async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_ = get_link()
    await context.bot.send_message(chat_id=chat_id, text=text_)


async def otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_ = get_otp()
    await context.bot.send_message(chat_id=chat_id, text=text_)


async def refresh_access_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    text_ = set_access_token(query)
    results = [
        InlineQueryResultArticle(
            id=query,
            title='Generate Access Token',
            input_message_content=InputTextMessageContent(text_)
        )]

    await context.bot.answer_inline_query(update.inline_query.id, results)


def build_and_run_app(msg=None):
    global application_
    global global_application_msg

    if msg is not None:
        global_application_msg = msg
    end_handler = CommandHandler('end', end)
    application_.add_handler(end_handler)

    link_handler = CommandHandler('link', link)
    application_.add_handler(link_handler)

    otp_handler = CommandHandler('otp', otp)
    application_.add_handler(otp_handler)

    refresh_access_token_handler = InlineQueryHandler(refresh_access_token)
    application_.add_handler(refresh_access_token_handler)

    job_queue = application_.job_queue

    if msg is not None:
        job_queue.run_once(send_msg, when=timedelta(seconds=6))

    job_queue.run_once(enable_command_msg, when=timedelta(seconds=10))
    job_queue.run_once(end_application, when=timedelta(minutes=commands_active_time))

    application_.run_polling()

    exit()


if __name__ == '__main__':
    build_and_run_app()
