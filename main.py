import asyncio
import logging
import sys
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from configurebot import cfg

TOKEN = cfg['token']

handler_button_new_question = cfg['button_new_question']
handler_button_about_us = cfg['button_about_us']

welcome_message = cfg['welcome_message']
error_message = cfg['error_message']
about_us = cfg['about_us']
question_first_msg = cfg['question_type_ur_question_message']

dev_id = cfg['dev_id']
teh_chat_id = cfg['teh_chat_id']
message_send = cfg['question_ur_question_send_message']

dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f'{welcome_message}', parse_mode='Markdown')


@dp.message(Command('help'))
async def get_help(message: Message):
    await message.answer('Как пользоваться? Очень просто.', parse_mode='Markdown')


def user_exists(user_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("SELECT 1 FROM clients WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None


def add_user(user_id, ban_status):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    if not user_exists(user_id):
        c.execute("INSERT INTO clients (id, is_ban) VALUES (?, ?)", (user_id, ban_status))
        conn.commit()
    else:
        print(f"User {user_id} already exists")
    conn.close()


def get_ban_status(user_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("SELECT is_ban FROM clients WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def set_ban_status(user_id, ban_status):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("UPDATE clients SET is_ban = ? WHERE id = ?", (ban_status, user_id))
    conn.commit()
    conn.close()


def unban_user(user_id):
    set_ban_status(user_id, 0)


@dp.message(Command('question', 'about_us', 'get_chat_id'))
async def client_new_question(message: Message):
    try:
        if message.text == '/question':
            if user_exists(message.from_user.id):
                if get_ban_status(message.from_user.id) == 1:
                    await message.answer("⚠ Вы *заблокированы* у бота!", parse_mode='Markdown')
                    return
                else:
                    await message.answer(f"{question_first_msg}")
            else:
                add_user(message.from_user.id, 0)
                await message.answer(f"{question_first_msg}")
        elif message.text == '/about_us':
            await message.answer(f"{about_us}", disable_web_page_preview=True, parse_mode='Markdown')
        elif message.text == '/get_chat_id':
            await message.answer(f"Chat id is: *{message.chat.id}*\nYour id is: *{message.from_user.id}*",
                                 parse_mode='Markdown')

    except Exception as e:
        c_id = message.chat.id
        await message.answer(f"{error_message}",
                             parse_mode='Markdown')
        await message.answer(dev_id, f"Случилась *ошибка* в чате *{c_id}*\nСтатус ошибки: `{e}`")


@dp.message(F.chat.type == 'private')
async def new_question(message: Message):
    if message.content_type == 'photo':
        user_massage = message.caption
    else:
        user_massage = message.text

    if message.chat.username is None:
        who = "Username не установлен"
    else:
        who = "@" + message.chat.username
    if message.content_type == 'photo':
        ph = message.photo[0].file_id
        await message.reply(f"{message_send}", parse_mode='Markdown')
        if user_massage is not None:
            await bot.send_message(teh_chat_id, f"✉ | Новый вопрос\nОт: {who}\nВопрос: "
                                                f"`{user_massage}`\n\n📝 Чтобы ответить на вопрос введите "
                                                f"`/ответ {message.chat.id} Ваш ответ`")
        await bot.send_photo(teh_chat_id, photo=ph)
    else:
        await message.reply(f"{message_send}", parse_mode='Markdown')

        await bot.send_message(teh_chat_id, f"✉ | Новый вопрос\nОт: {who}\nВопрос: "
                                            f"`{user_massage}`\n\n📝 Чтобы ответить на вопрос введите `/ответ "
                                            f"{message.chat.id} Ваш ответ`")


def extract_arg(arg):
    return arg.split()[1:]


@dp.message(F.text[:6] == '/ответ')
async def admin_ot(message: Message):
    try:
        args = extract_arg(message.text)
        if len(args) >= 2:
            chat_id = str(args[0])
            args.pop(0)
            answer = ""
            for ot in args:
                answer += ot + " "
            await message.reply('✅ Вы успешно ответили на вопрос! Сообщение отправлено клиенту')
            await bot.send_message(chat_id, f"✉ Новое уведомление!\nОтвет от тех.поддержки:\n\n`{answer}`",
                                   parse_mode='Markdown')
            return
        else:
            await message.reply('⚠ Укажите аргументы команды\nПример: `/ответ 123456789 Ваш ответ`',
                                parse_mode='Markdown')
            return
    except Exception as e:
        cid = message.chat.id
        await message.answer(f"{error_message}",
                             parse_mode='Markdown')
        await bot.send_message(dev_id, f"Случилась *ошибка* в чате *{cid}*\nСтатус ошибки: `{e}`",
                               parse_mode='Markdown')


@dp.message(F.text[:4] == '/бан')
async def admin_ban(message: types.Message):
    try:
        args = extract_arg(message.text)
        if len(args) >= 2:
            uid = int(args[0])
            reason = ' '.join(args[1:])
            if user_exists(message.from_user.id):
                set_ban_status(uid, 1)
                await message.reply(f'✅ Вы успешно заблокировали этого пользователя\nПричина: `{reason}`',
                                    parse_mode='Markdown')
                await bot.send_message(uid, f"⚠ Администратор *заблокировал* Вас в боте\nПричина: `{reason}`",
                                       parse_mode='Markdown')
                return
            else:
                await message.reply("⚠ Этого пользователя *не* существует!", parse_mode='Markdown')
                return
        else:
            await message.reply('⚠ Укажите аргументы команды\nПример: `/бан 123456789 Причина`',
                                parse_mode='Markdown')
            return
    except Exception as e:
        cid = message.chat.id
        await message.answer(f"{error_message}",
                             parse_mode='Markdown')
        await bot.send_message(dev_id, f"Случилась *ошибка* в чате *{cid}*\nСтатус ошибки: `{e}`",
                               parse_mode='Markdown')


@dp.message(F.text[:7] == '/разбан')
async def admin_unban(message: types.Message):
    try:
        args = extract_arg(message.text)
        if len(args) == 1:
            uid = int(args[0])
            if user_exists(uid):
                unban_user(uid)
                await message.reply(f'✅ Вы успешно разблокировали этого пользователя', parse_mode='Markdown')
                await bot.send_message(uid, f"⚠ Администратор *разблокировал* Вас в боте!", parse_mode='Markdown')
                return
            else:
                await message.reply("⚠ Этого пользователя *не* существует!", parse_mode='Markdown')
                return
        else:
            await message.reply('⚠ Укажите аргументы команды\nПример: `/разбан 123456789`', parse_mode='Markdown')
            return
    except Exception as e:
        cid = message.chat.id
        await message.answer(f"{error_message}",
                             parse_mode='Markdown')
        await bot.send_message(dev_id, f"Случилась *ошибка* в чате *{cid}*\nСтатус ошибки: `{e}`",
                               parse_mode='Markdown')


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
