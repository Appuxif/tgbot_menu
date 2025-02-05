import re

import plural_ru

from config import ya_money_url2 as ya_money_url, sber_card
from utils.bot_user_utils import update_msg_to_user, update_keyboard_to_user
from utils.spreadsheet import send_book_to_table
import utils.variables as variables
from utils.tour_questions import get_question

register_profile_questions_dict = {'registerTour': variables.register_tour_questions, }


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
        question = get_question(qi, variables.tour_list)
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

    # Проверка телефона
    if field == 'phone' or f == 'phone':
        # Проводить проверку в БД по номеру телефона
        if not(data == '-' and len(user['register']['persons_list']) != 1):
            data = validate_phone(data)
            if data is None:
                update_msg_to_user(user, {'text': 'Введите номер телефона в формате 7XXXXXXXXXX'})
                return True

    # Проверка количества брони
    if field == 'persons_amount' and int(data) > user['register']['tour_amount']:
        update_msg_to_user(user, {'text': 'Превышено допустимое количество человек для этого тура'})
        return True

    # Проверка возраста
    if f == 'age' and int(data) < user['register']['tour_age']:
        update_msg_to_user(user, {'text': 'Указанный возраст не подходит под условия тура'})
        return True

    # Проверка имени и фамилии
    if f == 'name' and len(data.split()) < 2:
        update_msg_to_user(user, {'text': 'Нужно ввести имя и фамилию в одном сообщении, разделя слова пробелом'})
        return True

    # Заполнение списка
    if field.endswith('_list'):
        last_item = user['register'].get(field, [{}])[-1]
        last_item[f] = data
        if last_item not in user['register'].get(field, []):
            user['register'][field] = user['register'].get(field, []) + [last_item]
    else:
        user['register'][field] = data
    if field not in user['fields_entered']:
        user['fields_entered'] += [field]


def check_answer_document(user, msg, question):
    """Проверка отправки изображения, аудио или видео"""
    if 'document' in user['register'] and (question['type'] == 'image' and
                                           # user['register']['document']['file_type'] in ['photo', 'document'] or
                                           user['register']['document']['file_type'] in ['photo'] or
                                           user['register']['document']['file_type'] == question['type']):
        # user['register'][question['name']] = user['register']['document']['file_url']
        user['register'][question['name']] = user['register']['document']['file_id']
        user['payment_confirmation_notification'] = True
        del user['register']['document']
        return False
    else:
        # if user.get('questions_document_done'):
        #     del user['questions_document_done']
        #     return False
        update_msg_to_user(user, {'text': f'Ответ на этот вопрос должен содержать {question["type"]}'})
        return True


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
    question = get_question(qi, variables.tour_list)
    if question['name'] == 'summary':
        success = register_summary(user)
        if not success:
            return True  # Если возникнет ошибка, то регистрация будет прервана
    elif question['name'] == 'register_done':
        # Завершение регистрации
        user['register']['tour_destination'] = 'tour_destination'
    user['register']['persons_list__len'] = user['register'].get('persons_list__len', 1)

    # Доступное количество тура
    if user['register'].get('tour') and not user['register'].get('tour_amount'):
        tour = [t for t in variables.tour_list if f'tour_{t[0]}' == user['register']['tour']][0]
        user['register']['tour_amount'] = int(tour[9]) - int(tour[10])
        user['register']['tour_age'] = int(tour[8])

    question_text = question['title'].format(user=user)

    # Отправляем следующий вопрос
    # conditions = question.get('conditions', {})
    # condition = all([isinstance(v, bool) and (f in user) == v or user.get(f) == v for f, v in conditions.items()])
    condition = eval(question.get('condition', 'True'))

    if condition:
        buttons = [(btn.get('text', btn.get('value')), btn['value']) for btn in question.get('buttons', [])]
        row_width = 1 if question['name'] in ['tour', 'payment_type'] else 2
        update_keyboard_to_user(user, {'buttons': buttons, 'text': question_text, 'row_width': row_width})
        return True
    else:
        # Пропуски вопросов, для которых не подходит условие
        if question['name'] == 'loop' and len(user['register']['persons_list']) < int(
                user['register']['persons_amount']):
            user['register']['persons_list'].append({})  # Добавляем новый объект для заполнения в опросе
            user['register']['persons_list__len'] += 1
            user['step'] -= 4
        else:
            user['step'] += 1
        if user['step'] < len(questions):
            send_next_question(user, questions)


def register_summary(user):
    """Действия, если question['name'] == 'summary'"""
    persons_amount = user["register"]["persons_amount"]
    persons_amount_plural = plural_ru.ru(int(persons_amount), ["место", "места", "мест"])
    tour = [t for t in variables.tour_list if f'tour_{t[0]}' == user['register']['tour']][0]
    user['register']['persons_amount_text'] = f'{persons_amount} {persons_amount_plural}'
    user['register']['tour_date'] = tour[2]
    user['register']['sum'] = get_summary_sum(user, tour)
    # user['register']['payment_link'] = f'{ya_money_url}{user["register"]["sum"]}'
    # user['register']['payment_link'] = f'{ya_money_url}'
    # user['register']['payment_link'] = f'Перевод на карту сбербанка: \n' \
    #                                    f'{sber_card}\n' \
    #                                    f'Оплата картой на сайте: {ya_money_url}'
    if user['register']['payment_type'] == 'payment_type_1':
        user['register']['payment_link'] = f'Перевод на карту сбербанка: \n{sber_card}'
    else:
        user['register']['payment_link'] = f'Оплата картой на сайте:\n{ya_money_url}'

    user['register']['tour_name'] = variables.call_data_translate.get(user['register']['tour'], user['register']['tour'])
    user['register']['tour_info'] = tour[7]

    # Отправка данных в таблицу
    try:
        send_book_to_table(user)
    except ValueError as err:
        if 'booking amount exceeded' in str(err):
            user['need_to_delete'] = True
            return update_msg_to_user(user, {'text': 'Превышено количество мест для тура. Кто-то вас опередил :(\n'
                                                     'Введите /start, чтобы начать заново'})
        raise err
    tour[10] = str(int(tour[10]) + len(user['register']['persons_list']))

    # Добавочные кнопки
    if tour[11]:
        addition_buttons = []
        for l in tour[11].splitlines():
            text, url = map(lambda x: x.strip(), l.split(':', 1))
            addition_buttons.append((text, 'none', url))
        update_keyboard_to_user(user, {'addition_buttons': addition_buttons})
    return True


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


def validate_phone(phone):
    """Функция приводит различное написание номеров телефонов к виду 79261234567"""
    phone = re.sub(r'[^\d]', '', phone)  # Удаляются все символы, которые не являются цифрой
    if len(phone) == 11 and phone.startswith('8'):
        phone = '7' + phone[1:]
    elif len(phone) == 10 and phone.startswith('9'):
        phone = '7' + phone
    elif len(phone) < 10:
        return None
    return phone


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
                  'image': check_answer_document,
                  # 'voice': check_answer_document,
                  # 'video': check_answer_document,
                  # 'coordinates': check_answer_coordinates,
                  }
