import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
telebot.apihelper.proxy = {'https': 'http://52.15.172.134:7778'}
token = '856621453:AAHtVJEIMsD5WZH9ytescn16_dYZajyluL4'
bot = telebot.TeleBot(token)


# тестовый список туров
tour_list = [
    '29 февраля-1 марта АБЗАКОВО-БАННОЕ (от 4900 руб.)',
    '7-8 марта ГУБАХА (от 3100 руб.)',
    '14-15 марта  ГУБАХА (от 3300 руб)',
    '21-31 марта КАМЧАТКА: ФРИРАЙД С ВУЛКАНОВ (от 49.000)',
    '8-11 марта СОЛНЕЧНЫЙ СОЧИ И АБХАЗИЯ (от 9700 руб)',
    '7 марта КАЧКАНАР И БУДДИЙСКИЙ МОНАСТЫРЬ (1900 руб.)',
    '8 марта ОЛЕНЬЯ ФЕРМА (1500 руб, 1300 руб детский)',
    '9 марта АРАКУЛЬСКИЙ ШИХАН: ВЕСНА (1500 руб)',
    '2-5 МАЯ ВЕСЕННИЙ КАЗАХСТАН - НУРСУЛТАН (от 8900 руб)',
    '9-11 МАЯ ЦВЕТУЩАЯ КАЗАНЬ (от 7200 руб)',
    '8-15 МАЯ АРМЕНИЯ И ГРУЗИЯ: САМОЕ КРАСИВОЕ И ВКУСНОЕ (от 39.000 руб.)',
    '12-14 ИЮНЯ ЛЕТНЯЯ КАЗАНЬ (от 7200 руб)'
]

menu1_list = [
    (1, 'Сырники 100/30гр',	110),
    (2, 'Блины простые 80гр', 70),
    (3, 'Блины с творогом 120гр', 100)
]

menu2_list = [
    (21, 'Смузи фруктовые(черника, СМОродина, малина) 300мл',	80),
    (22, 'Имбирный чай с апельсином 300мл', 60),
    (23, 'Компот из сухофруктов 300мл', 50)
]

payment_list = [
    'Лично курьеру',
    'Что-то еще'
]

users = {}


# Возвращает объект клавиатуры для телеграма
def make_keyboard(buttons, row_width=2):
    # buttons - массив с текстом кнопок
    markup = InlineKeyboardMarkup(row_width=row_width)
    btns = [InlineKeyboardButton(text=btn, callback_data=t + btn[:10]) for t, btn in buttons]
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
        # user = users.get(msg.from_user.id)
        # print(users)
        # if user is None:
        #     user = {}
        #     users.update({msg.from_user.id: user})
        #     print('Новый пользователь')

        print(f'{msg.message_id} {msg.chat.username}:{msg.from_user.first_name} '
              f'[{msg.chat.id}:{msg.from_user.id}]: {msg.text}')

        if '/start' in msg.text:
            user = {}
            users.update({msg.from_user.id: user})
            send_keyboard(
                msg,
                'Выберите тур',
                [('tour_', t) for t in tour_list],
                row_width=1
            )


def send_menu1(call):
    send_keyboard(
        call,
        'Выберите блюдо',
        # [('menu1_', f'{m[1]} {m[2]} ₽') for m in menu1_list] +
        [('menu1_', f'{m[0]}') for m in menu1_list] +
        [('menu1_clear_', 'Сбросить выбор'),
         ('menu1_done_', 'Завершить выбор')],
        row_width=1
    )


def edit_menu1_text(call, text, message_id):
    edit_keyboard(
        call,
        text,
        message_id,
        # [('menu1_', f'{m[1]} {m[2]} ₽') for m in menu1_list] +
        [('menu1_', f'{m[0]}') for m in menu1_list] +
        [('menu1_clear_', 'Сбросить выбор'),
         ('menu1_done_', 'Завершить выбор')],
        row_width=1
    )


def not_done_menu(call, user, item, menu):
    menu_list = menu1_list if menu == 'menu1' else menu2_list
    edit_menu_text = edit_menu1_text if menu == 'menu1' else edit_menu2_text
    for m in menu_list:
        if item in m[0]:
            user[menu] = user.get(menu, []) + [m]
            user[menu + '_bill'] = user.get(menu + '_bill', 0) + m[2]
            text_list = call.message.text.splitlines()
            text = '\n'.join(text_list[:-1]) + '\n'
            text += f"{m[1]} {m[2]} ₽"
            text += f"\nСумма: {user.get(menu + '_bill', 0)} ₽"
            edit_menu_text(call, text, call.message.message_id)
            break


def send_menu2(call):
    send_keyboard(
        call,
        'Выберите напиток',
        # [('menu2_', f'{m[1]} {m[2]} ₽') for m in menu2_list] +
        [('menu2_', f'{m[0]}') for m in menu2_list] +
        [('menu2_clear_', 'Сбросить выбор'),
         ('menu2_done_', 'Завершить выбор')],
        row_width=1
    )


def edit_menu2_text(call, text, message_id):
    edit_keyboard(
        call,
        text,
        message_id,
        [('menu2_', f'{m[0]}') for m in menu2_list] +
        [('menu2_clear_', 'Сбросить выбор'),
         ('menu2_done_', 'Завершить выбор')],
        row_width=1
    )


def construct_order_text(user):
    text = ''
    text += user.get("tour") + '\n\n'

    for m in user.get('menu1', []) + user.get('menu2', []):
        text += f"{m[1]} {m[2]} ₽\n"

    text += f"\nСумма: {user.get('menu1_bill', 0) + user.get('menu2_bill', 0)} ₽"
    return text


def send_confirm(call, user):
    text = 'Подтвердите выбор\n\n'
    text += construct_order_text(user)
    send_keyboard(
        call,
        text,
        [('fin_', 'Да'),
         ('fin_', 'Нет')],
        row_width=2
    )


def process_tour(call, user):
    tour = call.data.split('_')[1]
    for t in tour_list:
        if tour in t:
            user.update({'tour': t})
            break
    photo = open('menu.jpg', 'rb')
    bot.send_photo(
        call.from_user.id,
        photo,
        caption='Выберите блюдо',
        reply_markup=make_keyboard(
            [('menu1_', f'{m[0]}') for m in menu1_list] +
            [('menu1_clear_', 'Сбросить выбор'),
             ('menu1_done_', 'Завершить выбор')],
            row_width=1
        )

    )
    # send_menu1(call)
    # send_keyboard(
    #     call,
    #     'Выберите блюдо',
    #     # [('menu1_', f'{m[1]} {m[2]} ₽') for m in menu1_list] +
    #     [('menu1_', f'{m[0]}') for m in menu1_list] +
    #     [('menu1_clear_', 'Сбросить выбор'),
    #      ('menu1_done_', 'Завершить выбор')],
    #     row_width=1
    # )
    # bot.send_message(
    #     msg.from_user.id,
    #     text,
    #     reply_markup=make_keyboard(buttons, row_width)
    # )


def process_menu1(call, user):
    delete = True
    msg = call.message
    item = call.data.split('_')[-1]
    if 'menu1_clear_' in call.data:
        delete = False
        user['menu1'] = []
        user['menu1_bill'] = 0
        if msg.text != 'Выберите блюдо':
            edit_menu1_text(call, 'Выберите блюдо', msg.message_id)
    elif 'menu1_done_' not in call.data:
        delete = False
        not_done_menu(call, user, item, 'menu1')
    else:
        send_menu2(call)
    return delete


def process_menu2(call, user):
    delete = True
    msg = call.message
    item = call.data.split('_')[1]
    if 'menu2_clear_' in call.data:
        delete = False
        user['menu2'] = []
        user['menu2_bill'] = 0
        if msg.text != 'Выберите напиток':
            edit_menu2_text(call, 'Выберите напиток', msg.message_id)
    elif 'menu2_done_' not in call.data:
        delete = False
        not_done_menu(call, user, item, 'menu2')
    else:
        if user.get('menu1', []) or user.get('menu2', []):
            send_confirm(call, user)
        else:
            bot.send_message(call.from_user.id, 'Вы ничего не выбрали. Заказ сброшен. \n'
                                                'Введите /start, чтобы начать заново')
    return delete


def process_fin(call, user):
    item = call.data.split('_')[1]
    if 'Да' in item:
        user.update({'confirm': item})
        send_keyboard(
            call,
            'Выберите способ оплаты',
            [('pay_', m) for m in payment_list],
            row_width=1
        )
    else:
        bot.send_message(call.from_user.id, 'Вы не подтвердили заказ. Заказ сброшен. \n'
                                            'Введите /start, чтобы начать заново')


def process_pay(call, user):
    item = call.data.split('_')[1]
    for p in payment_list:
        if item in p:
            user.update({'payment': p})
    text = 'Спасибо! Ваш заказ будет ждать вас!\n\n'
    text += construct_order_text(user)
    text += f'\nСпособ оплаты: {user["payment"]}'
    text += '\n\nПо всем вопросам обращайтесь по телефону: 2-555-222\n' \
            'Для нового заказа введите /start'
    bot.send_message(
        call.from_user.id,
        text
    )
    print(user)
    # TODO: Отправка заказа в таблицу


# Функция обрабатывает нажатие кнопок на клавиатуре
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    delete = True

    msg = call.message  # Данные о сообщении с клавиатурой
    print(f'{call.from_user.id}:{call.from_user.username}:{call.from_user.first_name} '
          f'Кнопка {call.data} Сообщение {msg.message_id} Чат {msg.chat.id}')

    user = users.get(call.from_user.id)
    print(users)
    if user is None:
        bot.send_message(call.from_user.id, 'Произошла ошибка. \nВведите /start, чтобы начать заново')

    elif call.data.startswith('tour_'):
        process_tour(call, user)

    elif call.data.startswith('menu1_'):
        delete = process_menu1(call, user)

    elif call.data.startswith('menu2_'):
        delete = process_menu2(call, user)

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
