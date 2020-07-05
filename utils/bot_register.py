import plural_ru

from config import ya_money_url
from utils.bot_user_utils import update_msg_to_user, update_keyboard_to_user
from utils.spreadsheet import send_book_to_table
from utils.variables import register_tour_questions, tour_list, call_data_translate
from utils.tour_questions import get_question

register_profile_questions_dict = {'registerTour': register_tour_questions, }


def register_profile(user, msg):
    """Процесс регистрации профиля"""
    print('Регистрация', user['state'], user['step'])
    questions = register_profile_questions_dict[user['state']]
    return check_answer(user, msg, questions) or make_the_next_step(user, msg, questions)


def check_answer(user, msg, questions):
    """Проверка ответа на предыдущий вопрос"""
    if user['step'] > 0:
        if 'checked' in user:
            del user['checked']
            return False
        qi = questions[user['step'] - 1]
        question = get_question(qi, tour_list)
        return check_question_type(user, msg, question)


def check_question_type(user, msg, question):
    """Проверка типа ответа"""
    return question_types.get(question['type'], check_answer_another)(user, msg, question)


def check_answer_another(user, msg, question):
    """Проверка типа ответа для типов text, widget, message, num"""
    if 'buttons' in question:
        # Если ожидается нажатие кнопки, но был введен текст
        if not hasattr(msg, 'data'):
            update_msg_to_user(user, {'text': 'Воспользуйтесь клавиатурой'})
            return True
        # Если нажата кнопка страницы, то это не ответ, вопрос повторится, но с другой страницей
        if msg.data.startswith('page_') or msg.data == 'none':
            user['step'] -= 1
            return False

        # Если ответ должен быть булевый
        if question.get('isBool'):
            data = True if msg.data.lower() in ['1', 'true', 'да', 'yes'] else False
        else:
            data = msg.data
        field, f = question['name'], ''
    else:
        # Если ожидается текст, но была нажата кнопка
        if not hasattr(msg, 'text'):
            update_msg_to_user(user, {'text': 'Отправьте текст'})
            return True
        if question['type'] == 'num':
            try:
                float(msg.text)
            except ValueError:
                update_msg_to_user(user, {'text': 'Ответ на этот вопрос должен содержать только цифры. '
                                                  'Используйте точку для разделения дробей.'})
                return True
        if question['name'].startswith('persons_list'):
            field, f = question['name'].split('__')
        else:
            field, f = question['name'], ''
        data = msg.text

    if field.endswith('_list'):
        last_item = user['register'].get(field, [{}])[-1]
        last_item[f] = data
        if last_item not in user['register'].get(field, []):
            user['register'][field] = user['register'].get(field, []) + [last_item]
    else:
        user['register'][field] = data
    if question['name'] not in user['fields_entered']:
        user['fields_entered'] += [question['name']]


def make_the_next_step(user, msg, questions):
    """Следующий шаг в регистрации"""

    # Проверка отрицательного ответа на вопрос о сохранении данных и согласии
    del_mes = ''
    if user['register'].get('docAgreed') is False:
        del_mes = 'Вы не согласились принимать условия, регистрация окончена'
    elif user['register'].get('persons_amount') and int(user['register']['persons_amount']) <= 0:
        del_mes = 'Регистрация для 0 человек?! Серьезно? Регистрация окончена.'

    if del_mes:
        update_msg_to_user(user, {'text': del_mes})
        user['need_to_delete'] = True
        return True

    # Отправляем следующий вопрос, если необходимо
    if user['step'] < len(questions):
        send_next_question(user, questions)

    # Проверка окончания опроса
    # if user['step'] >= len(questions):
    #     # Конец регистрации. Оправляем главное меню
    #     return send_confirm_menu(user)
    #     # user[user['state']] = True
    #     # user['functions_to_process'] = user.get('functions_to_process', []) + ['registerProfileBase']
    #     # user['functions_to_process'] = user.get('functions_to_process', []) + [user['state']]

    user['step'] += 1
    return True


def send_next_question(user, questions):
    """Отправка следующего по счету вопроса"""
    # Выбор следующего вопроса для отправки
    qi = questions[user['step']]
    question = get_question(qi, tour_list)
    if question['name'] == 'summary':
        register_summary(user)
    elif question['name'] == 'register_done':
        # Завершение регистрации
        user['register']['tour_destination'] = 'tour_destination'
    user['register']['persons_list__len'] = user['register'].get('persons_list__len', 1)
    question_text = question['title'].format(user=user)

    # Отправляем следующий вопрос
    conditions = question.get('conditions', {})
    condition = all([isinstance(v, bool) and (f in user) == v or user.get(f) == v for f, v in conditions.items()])

    if condition:
        buttons = [(btn.get('text', btn.get('value')), btn['value']) for btn in question.get('buttons', [])]
        update_keyboard_to_user(user, {'buttons': buttons, 'text': question_text, 'row_width': 2})
    else:
        # Пропуски вопросов, для которых не подходит условие
        if question['name'] == 'loop' and len(user['register']['persons_list']) < int(user['register']['persons_amount']):
            user['register']['persons_list'].append({})  # Добавляем новый объект для заполнения в опросе
            user['register']['persons_list__len'] += 1
            user['step'] -= 3
        else:
            user['step'] += 1
        if user['step'] < len(questions):
            send_next_question(user, questions)


def register_summary(user):
    """Действия, если question['name'] == 'summary'"""
    persons_amount = user["register"]["persons_amount"]
    persons_amount_plural = plural_ru.ru(int(persons_amount), ["место", "места", "мест"])
    tour = [t for t in tour_list if f'tour_{t[0]}' == user['register']['tour']][0]
    user['register']['persons_amount_text'] = f'{persons_amount} {persons_amount_plural}'
    user['register']['tour_date'] = tour[2]
    user['register']['sum'] = get_summary_sum(user, tour)
    user['register']['payment_link'] = f'{ya_money_url}{user["register"]["sum"]}'
    user['register']['tour_name'] = call_data_translate.get(user['register']['tour'], user['register']['tour'])

    # Отправка данных в таблицу
    send_book_to_table(user)


def get_summary_sum(user, tour):
    """Расчет суммы брони тура"""
    price = tour[5] if len(user['register']['persons_list']) > 1 else tour[3]
    sum_ = 0
    for i, p in enumerate(user['register']['persons_list']):
        p['sum'] = 0
        p['price'] = int(price) if int(p['age']) > 14 else min(map(int, (tour[4], price)))
        sum_ += p['price']
    user['register']['persons_list'][0]['sum'] = sum_
    return sum_
# def send_confirm_menu(user):
#     """Отправка клавиатуры с подтверждением сохранения введенных данных"""
#     text = 'Были введены следующие данные \n\n'
#     for field in user['fields_entered']:
#         if translated_fields.get(field) and user.get(field) is not None:
#             from utils.yafunc_api import get_street_name
#             f = translated_fields[field]
#             if field == 'strID':
#                 v = get_street_name(user[field])
#             elif field == 'geoPoint':
#                 v = str(user[field])
#             elif field == 'tags':
#                 v = ', '.join([t['value'] for i, t in enumerate(user['tags'], 1) if t[f'tag{i}']])
#             elif isinstance(user[field], list):
#                 v = f'{len(user[field])} шт.'
#             else:
#                 v = ("Да" if user[field] is True else 'Нет') if isinstance(user[field], bool) else user[field]
#             text += f'{f}: {v}\n'
#     text += '\nЕсли все корректно, нажмите сохранить, или начните заново'
#     buttons = [('Сохранить введенные данные', 'processFunction'),
#                ('Начать заново', user['state'])]
#     # if user.get('registerProfileBase') is True:
#     buttons += [('Главное меню', 'main_menu')]
#     user['state'] = user['state'] + '_confirmation'
#     update_keyboard_to_user(user, {'buttons': buttons, 'text': text, 'row_width': 1})
#     del user['fields_entered']
#     return True

question_types = {'text': check_answer_another,
                  'widget': check_answer_another,
                  'message': check_answer_another,
                  'num': check_answer_another,
                  # 'tags': check_answer_another,
                  # 'action': check_answer_action,
                  # 'image': check_answer_document,
                  # 'voice': check_answer_document,
                  # 'video': check_answer_document,
                  # 'coordinates': check_answer_coordinates,
                  }
