from utils.variables import call_data_translate


def get_question(n, tour_list=None):
    """Запрашивает вопрос из базы вопросов"""
    q = questions[n].copy()
    if callable(q.get('buttons')):
        q['buttons'] = q['buttons'](tour_list)
    return q


def get_tour_buttons(tour_list):
    return [{'text': call_data_translate.get(f'tour_{t[0]}', t[1]), 'value': f'tour_{t[0]}'}
            for t in tour_list if int(t[10]) < int(t[9])]  # Проверка на превышение числа брони


questions = [
    # {'title': 'Введите Фамилию и Имя. Я забронирую тур на ваше имя.',
    #  'name': 'user_name',
    #  'type': 'text'},
    # 0
    {'title': 'Куда вы решили поехать?',
     'name': 'tour',
     'type': 'text',
     'buttons': get_tour_buttons},  # buttons будет заполнено при вызове вопроса
    # 1
    {'title': 'Доступно мест: {user[register][tour_amount]}\n'
              'Разрешенный возраст: {user[register][tour_age]}+\n'
              'Сколько мест нужно забронировать?\n\n'
              'Чтобы начать заново, введите /start',
     'name': 'persons_amount',
     'type': 'num'},
    # 2 Вводится, пока длина списка не будет равна persons_amount
    {'title': 'Напишите Фамилию и Имя туриста {user[register][persons_list__len]}',
     'name': 'persons_list__name',
     'type': 'text'},
    # 3
    {'title': 'Напишите телефон туриста {user[register][persons_list__len]} (или дефиз, чтобы пропустить)',
     'name': 'persons_list__phone',
     'type': 'text'},
    # 4
    {'title': 'Напишите число полных лет туриста {user[register][persons_list__len]}',
     'name': 'persons_list__age',
     'type': 'num'},
    # 5 Для зацикливания и выхода из цикла
    {'title': '',
     'name': 'loop',
     'type': 'none',
     'conditions': {'none_field': True}},
    # Отправить документ для ознакомления. Нужна ссылка на документ. Просто вставить ссылку в текст
    # {'title': 'Оплачивая тур вы соглашаетесь с нашими условиями бронирования. '
    #           'Вы принимаете ?',
    #  'name': 'docAgreed',
    #  'type': 'text',
    #  'isBool': True,
    #  'buttons': [{"value": "Да"}, {"value": "Нет"}]},
    # 6
    {'title': 'Ваш заказ: {user[register][persons_amount_text]} на {user[register][tour_name]}\n'
              '{user[register][tour_date]}.\n'
              'Итого к оплате: {user[register][sum]}\n'
              'Ссылка для оплаты: {user[register][payment_link]}\n'
              'Справа от суммы выбрать значок карты\n\n'
              'Оплачивая тур вы соглашаетесь с нашими <a href="https://vk.com/doc8962252_529848400?hash='
              '7d8dd7dc7e1a61eff6&dl=969edf1105c0622e9c">условиями</a> бронирования. ',
     'name': 'summary',
     'type': 'text',
     'buttons': [{"text": call_data_translate.get('payment_done', 'payment_done'), "value": "payment_done"}]},
    # 7
    {'title': 'Отправьте квитанцию об оплате, чтобы мы все проверили и сообщили вам о результате оплаты',
     'name': 'payment_confirmation',
     'type': 'image'},  # Тут нужна кастомная кнопка
    # 8
    {'title': 'Подождите. Как проверим квитанцию, вам придет уведомление. А пока можете забронировать другой тур.',
     'name': 'register_done',
     'type': 'text',
     'buttons': [{'text': call_data_translate.get('/start_register', '/start_register'), "value": "/start_register"}]},
    # {'title': 'Ура! Вы забронировали путешествие {user[register][tour_destination]}, {user[register][tour_date]}, '
    {'title': 'Вы забронировали путешествие {user[register][tour_name]}\n'
              'Дата: {user[register][tour_date]}\n\n'
              '{user[register][tour_info]}.\n\n'
              'За день до выезда, вечером, придет смс с информацией об отъезде.\n'
              'Остались вопросы? Звоните 8 923 355-78-99\n\n'
              'С любовью, ДоскиЛыжи.',
     'name': 'register_done',
     'type': 'text',
     'buttons': [{'text': call_data_translate.get('/start_register', '/start_register'), "value": "/start_register"}]},
]
