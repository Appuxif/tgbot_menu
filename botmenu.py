from urllib.parse import quote_plus, quote
from time import sleep
import requests

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import sheet_api_url, ya_money_url, token

# telebot.apihelper.proxy = {'https': 'http://52.15.172.134:7778'}

bot = telebot.TeleBot(token)


# тестовый список туров
tour_list = [
    # '29 февраля-1 марта АБЗАКОВО-БАННОЕ (от 4900 руб.)',
]

menu_dict = {}

payment_list = [
    ('0', 'Лично курьеру'),
    ('1', 'Оплата банковской картой')
]

users = {}


# Получение JSON из гугл таблицы
def get_data_from_sheet(params):
    r = requests.get(sheet_api_url+params)
    if r.status_code == 200:
        return r.json()
    return None


def get_tour_list_from_data(data):
    return [(d['index'], d['schedule']) for d in data['data']]


# Скачивает список туров из гугл таблицы
def get_tour_list():
    global tour_list
    data = None
    while data is None:
        data = get_data_from_sheet('?getData=1')
        if data:
            tour_list = get_tour_list_from_data(data)
            # print(tour_list)
        else:
            print('Список туров не получен')
            sleep(1)
# get_tour_list()


def get_menu_dict_from_data(data):
    i = 1
    menu_dict[f'menu{i}'] = []
    menu_dict['list'] = []
    for d in data['data']:
        if d['item']:
            menu_dict[f'menu{i}'].append((d['number'], d['item'], int(d['cost'][:-1])))
            menu_dict['list'].append((d['number'], d['item'], int(d['cost'][:-1])))
        else:
            i += 1
            menu_dict[f'menu{i}'] = []
    menu_dict['menus'] = i
    return menu_dict


# Скачивает меню из гугл таблицы
def get_menu_dict():
    global menu_dict
    data = None
    while data is None:
        data = get_data_from_sheet('?getData=2')
        if data:
            menu_dict = get_menu_dict_from_data(data)
        else:
            print('Список меню не получен')
            sleep(1)
# get_menu_dict()
# print('Гугл таблица загружена')


# Скачивает все доступные данные с гугл таблицы
def get_all():
    global menu_dict
    global tour_list
    data = None
    while data is None:
        data = get_data_from_sheet('?getAll=1')
        if data:
            tour_list = get_tour_list_from_data(data['schedule'])
            menu_dict = get_menu_dict_from_data(data['menu'])
        else:
            print('Данные не получены')
            sleep(1)
get_all()
print('Гугл таблица загружена')


# Возвращает объект клавиатуры для телеграма
def make_keyboard(buttons, row_width=2):
    # buttons - массив с текстом кнопок
    markup = InlineKeyboardMarkup(row_width=row_width)
    btns = [InlineKeyboardButton(text=btn_text, callback_data=btn_call) for btn_text, btn_call in buttons]
    markup.add(*btns)
    return markup


# Отправляет сообщение с клавиатурой
def send_keyboard(msg, text, buttons, row_width=2):
    return bot.send_message(
        msg.from_user.id,
        text,
        reply_markup=make_keyboard(buttons, row_width)
    )


# Редактирует отправленное сообщение с клавиатурой
def edit_keyboard(msg, text, edit_message_id, buttons, row_width=2):
    bot.edit_message_text(text, msg.from_user.id, edit_message_id, reply_markup=make_keyboard(buttons, row_width))


# Обработчик всех входящих сообщений
def listener(messages):
    for msg in messages:
        user = users.get(msg.from_user.id)

        print(f'{msg.message_id} {msg.chat.username}:{msg.from_user.first_name} '
              f'[{msg.chat.id}:{msg.from_user.id}]: {msg.text}')

        if '/start' in msg.text:
            user = {
                'state': 'wait_for_fio',
                'menu': 1
            }
            users.update({msg.from_user.id: user})
            bot.send_message(msg.from_user.id, 'Введите Фамилию и Имя, чтобы мы смогли отдать вам ваш заказ')
        elif user is not None and 'wait_for_fio' in user.get('state', ''):
            send_keyboard(
                msg,
                f'Вы ввели: {msg.text}\nПродолжаем?',
                [('Да', 'fio_1'),
                 ('Нет', 'fio_2')],
                row_width=2
            )
            user.update({
                'fio': msg.text,
                'state': ''
            })
        else:
            bot.send_message(msg.from_user.id, 'Чтобы оформить заказ, введите /start')


def get_menu_buttons(user):
    menui = f'menu{user["menu"]}'

    buttons = [(f'{m[1]} {m[2]} ₽', f'{menui}_{m[0]}') for m in menu_dict[menui]]
    if user['menu'] < menu_dict['menus']:
        buttons += [('СЛЕДУЮЩИЙ РАЗДЕЛ МЕНЮ', f'{menui}_next_')]
    buttons += [('СБРОСИТЬ ВЫБОР', f'{menui}_clear_')]
    buttons += [('ЗАВЕРШИТЬ ВЫБОР', f'{menui}_done_')]
    return buttons


def send_menu_photo(call, user):
    bot.send_photo(
        call.from_user.id,
        open('menu.jpg', 'rb'),
        caption='Ознакомтесь с меню',
        reply_markup=make_keyboard(
            [('Отлично, пора выбирать!', 'photo_done')],
            row_width=1
        )
    )


def send_menu1(call, user):
    text = 'Выберите блюдо\n'
    text += generate_menu_text(user)
    send_keyboard(
        call,
        text,
        get_menu_buttons(user),
        row_width=1
    )


def edit_menu1_text(call, user, message_id):
    text = 'Выберите блюдо\n'
    text += generate_menu_text(user)
    edit_keyboard(
        call,
        text,
        message_id,
        get_menu_buttons(user),
        row_width=1
    )


def generate_menu_text(user):
    text = ''
    if user.get('menu_list', []):
        text += '\n'
        for m in user.get('menu_list', []):
            text += f"{m[1]} {m[2]} ₽\n"
    text += f"\nСумма: {user.get('menu_bill', 0)} ₽"
    return text
    # text = '\n'.join(text_list[:-1]) + '\n'


# text += f"{m[1]} {m[2]} ₽"
# text += f"\nСумма: {user.get('menu_bill', 0)} ₽"

def not_done_menu(call, user, item):
    for m in menu_dict['list']:
        if item in m[0]:
            user['menu_list'] = user.get('menu_list', []) + [m]
            user['menu_bill'] = user.get('menu_bill', 0) + m[2]
            edit_menu1_text(call, user, call.message.message_id)
            break


def construct_order_text(user):
    text = ''
    text += user.get('fio') + '\n'
    text += user.get("tour") + '\n'
    text += generate_menu_text(user)
    return text


def send_confirm(call, user):
    if user.get('menu_list', []):
        text = 'Подтвердите выбор\n\n'
        text += construct_order_text(user)
        send_keyboard(
            call,
            text,
            [('Да', 'fin_1'),
             ('Нет', 'fin_2')],
            row_width=2
        )
    else:
        bot.send_message(call.from_user.id, 'Вы ничего не выбрали. Заказ сброшен. \n'
                                            'Введите /start, чтобы начать заново')


def process_fio(call, user):
    item = call.data.split('_')[1]
    if '1' in item:
        send_keyboard(
            call,
            'Выберите тур',
            [(t[1], f'tour_{t[0]}') for t in tour_list],
            row_width=1
        )
    else:
        bot.send_message(call.from_user.id, 'Вы не подтвердили Фамилию и Имя. Заказ сброшен. \n'
                                            'Введите /start, чтобы начать заново')


def process_tour(call, user):
    tour = call.data.split('_')[1]
    for t in tour_list:
        if int(tour) == t[0]:
            user.update({'tour': t[1]})
            break
    send_menu_photo(call, user)


def process_photo(call, user):
    send_menu1(call, user)
    pass


def process_menu1(call, user):
    delete = True
    msg = call.message
    item = call.data.split('_')[-1]
    menui = f'menu{user["menu"]}'
    if f'{menui}_clear_' in call.data:
        delete = False
        user['menu'] = 1
        user['menu_list'] = []
        user[f'menu_bill'] = 0
        if msg.text != 'Выберите блюдо':
            edit_menu1_text(call, user, msg.message_id)
    elif f'{menui}_next_' in call.data:
        if user['menu'] < menu_dict['menus']:
            user['menu'] += 1
            send_menu1(call, user)
        else:
            send_confirm(call, user)
    elif f'{menui}_done_' in call.data:
        send_confirm(call, user)
    else:
        delete = False
        not_done_menu(call, user, item)
    return delete


def process_fin(call, user):
    item = call.data.split('_')[1]
    if '1' in item:
        user.update({'confirm': item})
        send_keyboard(
            call,
            'Выберите способ оплаты',
            [(m[1], f'pay_{m[0]}') for m in payment_list],
            row_width=1
        )
    else:
        bot.send_message(call.from_user.id, 'Вы не подтвердили заказ. Заказ сброшен. \n'
                                            'Введите /start, чтобы начать заново')


def process_pay(call, user):
    item = call.data.split('_')[1]
    for p in payment_list:
        if item in p[0]:
            user.update({'payment': p[1]})
    if item == '0':
        text = 'Спасибо! Ваш заказ будет ждать вас!\n\n'
        text += construct_order_text(user)
        text += f'\nСпособ оплаты: {user["payment"]}'
    else:
        text = 'Спасибо! Вы выбрали оплату банковской картой. ' \
               'Произведите оплату и тогда ваш заказ будет ждать вас!\n\n'
        text += construct_order_text(user)
        text += f'\nСпособ оплаты: {user["payment"]}'
        text += f'\nСсылка для оплаты: {ya_money_url}{user["menu_bill"]}'
        text += f'\nВ поле "Комментарий" обязательно укажите Фамилию и Имя, чтобы мы смогли вас идентифицировать'
    text += '\n\nПо всем вопросам обращайтесь по телефону: +7 (950) 544-74-73\n' \
            'Для нового заказа введите /start'
    bot.send_message(
        call.from_user.id,
        text,
        disable_web_page_preview=True
    )
    user['tg'] = f"{call.from_user.id} {call.from_user.username} " \
                 f"{call.from_user.first_name} {call.from_user.last_name}"
    print(user)
    send_order_to_table(user)


def send_order_to_table(user):
    user["menu_bill"] = str(user["menu_bill"])
    params = f'?addOrder=1' \
             f'&tour={quote_plus(user["tour"][:20] + "...")}' \
             f'&fio={quote_plus(user["fio"])}' \
             f'&bill={quote_plus(user["menu_bill"])}' \
             f'&payment={quote_plus(user["payment"])}' \
             f'&tg={quote_plus(user["tg"])}'
    for m in user['menu_list']:
        params += f'&list={quote_plus(m[1])}'
    data = get_data_from_sheet(params)
    print(data)


# Функция обрабатывает нажатие кнопок на клавиатуре
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    delete = True

    msg = call.message  # Данные о сообщении с клавиатурой
    print(f'{call.from_user.id}:{call.from_user.username}:{call.from_user.first_name} '
          f'Кнопка {call.data} Сообщение {msg.message_id} Чат {msg.chat.id}')

    user = users.get(call.from_user.id)
    # print(users)
    if user is None:
        bot.send_message(call.from_user.id, 'Произошла ошибка. \nВведите /start, чтобы начать заново')
    elif call.data.startswith('fio_'):
        process_fio(call, user)

    elif call.data.startswith('tour_'):
        process_tour(call, user)

    elif call.data.startswith('photo_'):
        process_photo(call, user)

    elif call.data.startswith('menu'):
        delete = process_menu1(call, user)

    elif call.data.startswith('fin_'):
        process_fin(call, user)

    elif call.data.startswith('pay_'):
        process_pay(call, user)

    if delete:
        bot.delete_message(call.from_user.id, msg.message_id)
    bot.answer_callback_query(call.id)


bot.set_update_listener(listener)
# Для запуска локально, вне яндекс функции
if __name__ == '__main__':

    bot.remove_webhook()
    bot.polling()
