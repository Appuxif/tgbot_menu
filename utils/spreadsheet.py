from datetime import datetime, timezone
from time import sleep, monotonic
from urllib.parse import quote_plus
from uuid import uuid4

import requests

from config import sheet_api_url
from utils.myworkers import MyWorkers

book_worker = MyWorkers(1)


# Получение JSON из гугл таблицы
def get_data_from_sheet(params, method='GET'):
    if method == 'GET':
        r = requests.get(sheet_api_url + params)
    elif method == 'POST':
        r = requests.post(sheet_api_url, json=params)
    if r.status_code == 200:
        if 'application/json' in r.headers['Content-Type']:
            return r.json()
        else:
            print(r.text)
            raise TypeError('Something wrong with request to table')
    return None


def get_tour_list_from_data(data):
    # return [(d['index'], d['schedule']) for d in data['data']]
    l = [list(d.values()) for d in data['data']]
    for r in l:
        r[3], r[4], r[5] = int(r[3]), int(r[4] or r[3]), int(r[5] or r[3])
        r[8], r[9], r[10] = int(r[8]), int(r[9]), int(r[10] or 0)
    return l


def get_menu_dict_from_data(data):
    i = 1
    menu_dict = {f'menu{i}': [], 'list': []}
    for d in data['data']:
        if d['item']:
            menu_dict[f'menu{i}'].append((d['number'], d['item'], int(d['cost'][:-1])))
            menu_dict['list'].append((d['number'], d['item'], int(d['cost'][:-1])))
        else:
            i += 1
            menu_dict[f'menu{i}'] = []
    menu_dict['menus'] = i
    return menu_dict


def get_tour_list():
    # global tour_list
    data = None
    while data is None:
        data = get_data_from_sheet('?getData=1')
        if data:
            tour_list = get_tour_list_from_data(data)
            return tour_list
            # print(tour_list)
        else:
            print('Список туров не получен')
            sleep(1)


# Скачивает все доступные данные с гугл таблицы
def get_all():
    # global menu_dict
    # global tour_list
    data = None
    while data is None:
        data = get_data_from_sheet('?getAll=1')
        if data:
            tour_list = get_tour_list_from_data(data['schedule'])
            menu_dict = get_menu_dict_from_data(data['menu'])
            return menu_dict, tour_list
        else:
            print('Данные не получены')
            sleep(1)
    return None, None


# Скачивает меню из гугл таблицы
def get_menu_dict():
    data = None
    while data is None:
        data = get_data_from_sheet('?getData=2')
        if data:
            menu_dict = get_menu_dict_from_data(data)
            return menu_dict
        else:
            print('Список меню не получен')
            sleep(1)


def send_order_to_table(user):
    """Строго для botmenu"""
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


def send_book_to_table(user):
    """Отправка брони тура. Строго для bottour"""
    now = datetime.now(tz=timezone.utc).isoformat()
    user['register']['payment_id'] = str(uuid4()).replace('-', '')[:6]
    request = {
        'method': 'addBook',
        'tour': user['register']['tour_name'][:20],
        'p_list': [[now, user['tg']] + p['name'].split(' ', 1) + list(p.values())[1:] +
                   [user['register']['payment_id'], 'Ожидание оплаты']
                   for p in user['register']['persons_list']]
    }
    data = {}
    book_worker.add_task(_send_book_to_table, (request, data))
    timer = monotonic()
    while not data:
        if monotonic() - timer > 30:
            raise TimeoutError('Too long response')
        sleep(0.3)
    print('Ответ от GAS', data)
    if not('msg' in data and data['msg'] == 'OK'):
        raise ValueError(data)


def _send_book_to_table(request, response):
    """Вспомогательная функция для отправки брони асинхронно"""
    data = get_data_from_sheet(request, 'POST')
    response.update(data)


def send_payment_accept(tour, payment_id, method=None):
    method = method or 'acceptPayment'
    request = {
        'method': method,
        'tour': tour[:20],
        'paymentID': payment_id
    }
    data = get_data_from_sheet(request, 'POST')
    print('Ответ от GAS', data)
    if not ('msg' in data and data['msg'] == 'OK'):
        raise ValueError(data)

