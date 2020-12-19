import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    
)
from dotenv import load_dotenv
from gtts import gTTS
import os
import time

from pasta_bot_db import (
    add_user,
    user_exists, 
    get_last_post_id, 
    remove_user,
    get_username,
    get_last_read,
    get_post_text,
    update_last_read) 
#load .env
load_dotenv()
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)  
GREETINGS_TEXT = """
                    Самое время рассказать, что это за бот.
                    Сложные алгортмы, неорсети, машинное обучение, глубокий анализ ВСЕХ ваших данных людьми и машинами
                    (включая личные переписки, фотографии на этом девайсе как и все иные доступные базы данных)
                    смогут помочь определить ВАШИ любимые пасты. Если вам не комфортно, что бы ваши данные подверглись
                    анализу нажмите НЕТ, если же вам нечего скрывать нажмите кнопку FRESH PASTA
                    """
AUTH, INTRO, UPDATE, POST_DETAIL, FRESH_PASTA = range(5)

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_exists(user_id=user_id):
        username = get_username(user_id)
        text = 'Привет!'+username+'. Добро пожаловать. Снова. комманда /update покажет сколько у Вас непрочитанных паст.'
        update.message.reply_text(
        text,)
        return UPDATE
    else:
        text = """
        Привет друг! Перед началом работы бота, нам нужно познакомиться. Напиши свое имя или команду /skip 
        если хочешь пропустить регистрацию 
        """
        update.message.reply_text(
            text,
        )
        return AUTH

def skip_signup(update: Update, context: CallbackContext):
    username = update.effective_user.first_name
    new_user = (update.effective_user.id, username, get_last_post_id())
    print(new_user, 'user was added')
    add_user(user=new_user)
    update.message.reply_text(f'Хорошо. Тогда я буду называть тебя хуйлом. Понял? Впадлу блять ему имя свое написать в телеге. Хотяя.. {username} звучит куда обиднее лол. Будешь значит записан как {username}')
    time.sleep(3)
    reply_keyboard = [['FRESH_PASTA', 'Fresh_pasta']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        text=GREETINGS_TEXT,
        reply_markup = markup,
    )
    return INTRO

def signup(update: Update, context: CallbackContext):
    username = update.message.text
    new_user = (update.effective_user.id, username, get_last_post_id())
    print(new_user)
    add_user(user=new_user)
    reply_keyboard = [['FRESH_PASTA', 'Fresh_pasta']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(f'Спасибо,{username} я учту.')
    #time.sleep(3)
    update.message.reply_text(GREETINGS_TEXT, reply_markup=markup)
    return INTRO
                                                                                               
def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    remove_user(user=(user.id,))
    print(user.id, "was deleted from the database")
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def intro(update: Update, context: CallbackContext) -> int:
    text = 'Вы точно ввели команду /fresh_pasta?' 
    reply_keyboard = [['Да', 'Yes']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(text, reply_markup=markup)
    return UPDATE

def update(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    last_post_id = get_last_post_id()
    last_read = get_last_read(user_id)
    unread_posts_count = last_post_id - last_read + 1
    text = f'you have {unread_posts_count} unread posts'
    if unread_posts_count > 0:
        markup = ReplyKeyboardMarkup([['/FRESH_PASTA']], one_time_keyboard=True)
        update.message.reply_text(
            text=text+"\nчто бы прочесть следующую пасту нажми fresh_pasta",
            reply_markup = markup
        )
        return FRESH_PASTA
    else:
        markup = ReplyKeyboardRemove()
        update.message.reply_text(
            text=text+"\nпопробуй команду /update позже. ",
            reply_markup = markup
        )
        

def fresh_pasta(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    last_read = get_last_read(user_id)
    post_text = get_post_text(last_read)
    update_last_read(user_id)
    message = 'Если пасту лень читать нажми кнопку /audio. (может занять какое-то время)\nЧто бы посмотреть оставшиеся пасты нажми /update'
    if len(post_text) > 4096:
        for x in range(0, len(post_text), 4096):
            update.message.bot.send_message(chat_id=update.effective_chat.id, text=post_text[x:x+4096])
        update.message.bot.send_message(chat_id=update.effective_chat.id, text=message) 
        return POST_DETAIL
    else:
        update.message.bot.send_message(chat_id=update.effective_chat.id, text=post_text)
        update.message.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return POST_DETAIL
    
def audio(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    last_read = get_last_read(user_id)
    post_text = get_post_text(last_read-1)
    if os.path.exists(f"/audio/{last_read-1}.ogg"):
        print('file exists.Sending...')
    else:
        print('file not found. creating..')
        tts = gTTS(post_text, lang='ru' )
        update.message.bot.send_message(chat_id=update.effective_chat.id, text='заставлем малую наговаривать в микрофон. Погоди мальца...')
        tts.save(f'audio/{last_read-1}.ogg')
    update.message.bot.send_voice(chat_id=update.effective_chat.id, voice=open(f'audio/{last_read-1}.ogg', 'rb'))
    update.message.reply_text(
        text = 'нажми /update что бы посмотреть оставшиеся посты.'
    )
    return UPDATE


def main():
    updater = Updater(token=TG_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AUTH:[CommandHandler('skip', skip_signup), MessageHandler(Filters.text & ~Filters.command, signup)],
            INTRO:[MessageHandler(Filters.text & ~Filters.command, intro)],
            UPDATE:[MessageHandler(Filters.text & ~Filters.command, update), CommandHandler('update', update)],
            POST_DETAIL: [CommandHandler('audio', audio), CommandHandler('update', update)],
            FRESH_PASTA: [CommandHandler('FRESH_PASTA', fresh_pasta)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()