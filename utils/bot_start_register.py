def start_register_tour(user, msg):
    """Начало регистрации брони тура"""
    user.clear()
    user.update({'step': 0, 'state': 'registerTour', 'fields_entered': [], 'register': {}})
    user['tg'] = f'{msg.from_user.id} {msg.from_user.username or ""} ' \
                 f'{msg.from_user.first_name or ""} {msg.from_user.last_name or ""}'
    user['telegramID'] = msg.from_user.id


def start_test_register_tour(user):
    """Тестовая регистрация с заполненными полями"""
    user.clear()
    user.update({'step': 7, 'state': 'registerTour',
                 'fields_entered': ['tour', 'persons_amount', 'persons_list__name',
                                    'persons_list__phone', 'persons_list__age'],
                 'register': {'persons_list__len': 3, 'tour': 'tour_2', 'persons_amount': '3',
                              'persons_list': [{'name': 'Фамилия Имя 1', 'phone': '123', 'age': '12'},
                                               {'name': 'Фамилия Имя 2', 'phone': '123321', 'age': '14'},
                                               {'name': 'Фамилия Имя 3', 'phone': '211221', 'age': '21'}]},
                 'last_activity': '2020-07-05T09:10:31.504570+00:00'})
