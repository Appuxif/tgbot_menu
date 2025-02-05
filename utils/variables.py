menu_dict = tour_list = None
register_tour_questions = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

call_data_translate = {
    '/start_register': 'Забронировать!',
    'payment_done': 'Оплачено',
    'payment_type_1': 'Перевод на карту сбербанка',
    'payment_type_2': 'Оплата по карте через сайт',
}


def update_variables():
    from utils.spreadsheet import get_all
    global menu_dict, tour_list
    menu_dict, tour_list = get_all()
    # print(menu_dict)
    # print(tour_list)
    call_data_translate.update({f'tour_{t[0]}': t[1] for t in tour_list})
    return menu_dict, tour_list


update_variables()
