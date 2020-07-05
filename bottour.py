from datetime import datetime, timezone
import requests

from telebot.types import (InlineKeyboardMarkup, InlineKeyboardButton)
import telebot

from config import token2 as token

# telebot.apihelper.proxy = {'https': 'http://52.15.172.134:7778'}
from utils.bot_register import register_profile_questions_dict, register_profile, update_variables
from utils.bot_start_register import start_register_tour, start_test_register_tour
from utils.bot_user_utils import update_keyboard_to_user
from utils.variables import call_data_translate

bot = telebot.TeleBot(token)

# тестовый список туров
# tour_list = [
#     # '29 февраля-1 марта АБЗАКОВО-БАННОЕ (от 4900 руб.)',
# ]


# menu_dict = {}
# payment_list = [
#     ('0', 'Лично курьеру'),
#     ('1', 'Оплата банковской картой')
# ]
users = {}
debug = False
update_variables()


def process_msg(msg):
    """Обработка сообщений от телеграма"""
    if debug and msg.from_user.id != 432134928:
        return
    # Поиск пользователя по user_id
    if getattr(msg, 'text', '') == '/start':
        if msg.from_user.id in users:
            users.pop(msg.from_user.id)
    user = get_or_create_user(msg)
    print(user)

    # Проверка сессии на устаревание
    now = datetime.now(tz=timezone.utc)
    # then = now if 'last_activity' not in user else datetime.fromisoformat(user['last_activity'])
    # diff = now - then
    # st = user.get('state', '')
    # Не сбрасывать сессию при ожидании оплаты
    # if st != 'main_menu' and not st.endswith('BillQr_image') and diff.seconds > 3600:  # Время сессии - 1 час
    #      bot.send_message(user, 'Ваша сессия устарела. Введите /start чтобы начать снова')
    # else:
    #     # Обработка сообщения от телеграма
    do_processing(user, msg)
    user['last_activity'] = now.isoformat()

    # Ответ пользователю
    answer_to_user(user, msg)

    # Сохранение пользователя в БД
    if user.get('need_to_delete', False) is True:
        print('Пользователь удален из базы бота')
        users.pop(msg.from_user.id)
    else:
        users[msg.from_user.id] = user


def get_or_create_user(msg):
    """Находит в базе или создает ногово пользователя в коллекции пользователей бота"""
    user = users.get(msg.from_user.id)
    if user is None:
        print("Новый пользователь")
        # user = {'state': 'wait_for_fio', 'menu': 1}
        user = {'state': 'new_user'}
        users[msg.from_user.id] = user
        if (getattr(msg, 'text', '') or getattr(msg, 'data', '')) != '/start_register':
            bot.send_message(msg.from_user.id, 'Привет, я бот ДоскиЛыжи, что поможет быстро и легко забронировать '
                                               'себе место в крутом путешествии!',
                             reply_markup=make_keyboard({'buttons': [('Забронировать!', '/start_register')]}))
    return user


def do_processing(user, msg):
    """Обработка сообщения от телеграма. Выполнение действия в соответствии с текущим состоянием пользователя"""
    # Обработка команд
    if process_msg_text(user, msg):
        return

    # Обработка кнопок
    if process_call_data(user, msg):
        return

    # # Обработка документов, изображений, войсов и видео
    # if process_document(user, msg):
    #     return

    # # Обработка локации
    # if process_coordinates(user, msg):
    #     return

    # Обработка регистраций
    if process_registration(user, msg):
        return

    # if getattr(msg, 'call', '') or '':
    #     return send_main_menu(user)


def process_msg_text(user, msg):
    """Обработка введенных пользователем комманд"""
    msg_text = (getattr(msg, 'text', '') or '')
    if not msg_text:
        return False
    # Инициализация пользователя для неизвестного пользователя или по команде /start_register
    print('Получен текст')
    # if '/start_test' in msg_text:
    #     start_test_register_tour(user)
    #     msg.data = 'Да'
    #     return

    if '/start_register' in msg_text:
        return start_register_tour(user)
    # elif '/main_menu' in msg_text:
    #     return send_main_menu(user)


def process_call_data(user, msg):
    """Обработка нажатий на кнопку"""
    call_data = getattr(msg, 'data', '') or ''
    if not call_data:
        return False
    print('Получено нажатие на кнопку')
    if call_data:
        if call_data == '/start_register':
            return start_register_tour(user)
        elif call_data.startswith('page_'):
            return update_keyboard_to_user(user, {'page': int(call_data.split('_')[1])})
        elif call_data == 'registerTour':
            return start_register_tour(user)
        # elif call_data == 'register_continue':
        #     return register_continue(user, msg)
        # elif call_data == 'questions_document_done':
        #     user['questions_document_done'] = True
        # elif call_data == 'questions_tag_done':
        #     user['questions_tag_done'] = True
        # elif call_data == 'processFunction':
        #     return process_function_action(user)
    return False


def process_registration(user, msg):
    """Обработка регистрации профиля"""
    if user['state'] in register_profile_questions_dict:
        register_profile(user, msg)


# def process_document(user, msg):
#     """Обработка отправленных документов и изображений"""
#     document = get_document_from_msg(msg)  # r.content
#     if document:
#         print('Получен документ')
#         # if user['state'] == 'getElectricityBillQr_image':
#         if user['state'].startswith('get') and user['state'].endswith('BillQr_image'):
#             # Скачивание изображения из сообщения
#             print('Получение квитанции об оплате')
#             qr_type = user['state'][3:].split('Bill')[0].lower()
#             return get_bill_qr_image(user, msg, document, qr_type)
#         elif user['state'] == 'registerProfileElectricityCount' or 'registerProfileVotingDocument':
#             user['document'] = document
#             return False
#     elif document is None:
#         print('Не удалось получить документ')
#         bot.send_message(msg.from_user.id, 'Не удалось получить документ. '
#                                            'Попробуйте еще раз или обратитесь в поддержку.')
#     elif document is False:
#         return False


# def process_coordinates(user, msg):
#     """Обработка отправленной локации"""
#     location = getattr(msg, 'location', None)
#     if location:
#         print(f'Получена локация {location.latitude} {location.longitude}')
#         user['coordinates'] = (location.longitude, location.latitude)
#     return False


def answer_to_user(user, msg):
    """Отправка ответа пользователю, если нужно"""
    # if 'functions_to_process' in user:
    #     print('Обработка функции')
    #     for function in user['functions_to_process']:
    #         process_function(user, function)
    #     del user['functions_to_process']

    if 'msg_to_user' in user:
        bot.send_message(msg.from_user.id, text=user['msg_to_user']['text'],
                         parse_mode=user['msg_to_user'].get('parse_mode', 'HTML'))
        del user['msg_to_user']

    if 'keyboard_to_user' in user:
        bot.send_message(msg.from_user.id,
                         user['keyboard_to_user']['text'],
                         parse_mode=user['keyboard_to_user'].get('parse_mode', 'HTML'),
                         # reply_markup=make_keyboard(user['keyboard_to_user'].get('buttons', []),
                         #                            user['keyboard_to_user'].get('row_width', 2),
                         #                            user['keyboard_to_user'].get('page', 0)))
                         reply_markup=make_keyboard(user['keyboard_to_user']))
        del user['keyboard_to_user']


# def make_keyboard(buttons, row_width=2, page=0):
def make_keyboard(keyboard_to_user):
    """Генерирует клавиатуру для отправки пользователю. Распределяет кнопки по страницам, если кнопок много"""
    # buttons - массив с текстом кнопок
    buttons = keyboard_to_user.get('buttons', [])
    row_width = keyboard_to_user.get('row_width', 2)
    page = keyboard_to_user.get('page', 0)
    addition_buttons = keyboard_to_user.get('addition_buttons', [])
    page_len = 10
    # if buttons:
    markup = InlineKeyboardMarkup(row_width=row_width)
    markup.add(*[InlineKeyboardButton(text=text, callback_data=call)
                 for text, call in buttons[page_len * page: page_len * page + page_len]])
    pages = len(buttons) // page_len + (
        1 if len(buttons) % page_len != 0 else 0)  # По page_len элементов на страницу
    if pages > 1:
        markup.row(InlineKeyboardButton(text=f'Страница {page + 1} из {pages}', callback_data='none'))
        markup.add(*[InlineKeyboardButton(text=i + 1, callback_data=f'page_{i}') for i in range(pages)])

    markup.add(*[InlineKeyboardButton(text=btn[0], callback_data=btn[1]) for btn in addition_buttons])
    return markup


# def get_document_from_msg(msg):
#     """Получение и скачивание документа, фото, вижел или голоса из сообщения"""
#     for file_type in ['document', 'photo', 'video', 'voice']:
#         file = getattr(msg, file_type, None)
#         if file:
#             if file_type == 'photo':
#                 file = file[1]
#             break
#     else:
#         return False
#
#     file_id = file.file_id
#     file_info = bot.get_file(file_id)
#     file_name = 'bot{0}/{1}'.format(bot.token, file_info.file_path)
#     file_url = 'https://api.telegram.org/file/{}'.format(file_name)
#     return {'file_url': file_url, 'file_name': file_name, 'file_type': file_type}
#     # r = requests.get(file_url, proxies=telebot.apihelper.proxy)
#     # if r.status_code == 200:
#     #     return {'content': r.content, 'file_url': file_url, 'file_name': file_name}
#     # return None


#######################################################################################
def listener(messages):
    """Прослушивает все входящие боту сообщения и выводит текст в консоль"""
    for msg in messages:
        print(f'{msg.message_id} {msg.chat.username}:{msg.from_user.first_name} '
              f'[{msg.chat.id}:{msg.from_user.id}]: {msg.text}')


@bot.message_handler(content_types=["text", "photo", "document", 'voice', 'video', 'location'])
def text_message(msg):
    """Обработка текстовых сообщений"""
    c = 0
    while True:
        try:
            process_msg(msg)
            break
        except (requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout) as err:
            print(str(err))
            c += 1
            if c > 3:
                raise err
        except Exception as err:
            bot.send_message(msg.from_user.id, 'Произошла ошибка. Скоро она будет решена. '
                                               'Попробуйте позже или обратитесь в поддержку.')
            text = f'{str(err)}\n{msg.from_user.id}: {getattr(msg, "text", None) or getattr(msg, "data", None)}'
            bot.send_message(432134928, text)
            raise err


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    """Обработка нажатий кнопок на кливиатуре"""

    bot.answer_callback_query(call.id)
    if call.data != 'none':
        print(f'{call.from_user.id}:{call.from_user.username}:{call.from_user.first_name} '
              f'Кнопка {call.data} Сообщение {call.message.message_id} Чат {call.message.chat.id}')
        text_message(call)
        # bot.delete_message(call.from_user.id, call.message.message_id)
        text = call.message.text + '\n\n> ' + call_data_translate.get(call.data, call.data)
        bot.edit_message_text(text, call.from_user.id, call.message.message_id)


bot.set_update_listener(listener)

if __name__ == '__main__':
    debug = True
    print('working')
    bot.polling()
