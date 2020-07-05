def user_has_changed(user, old_user):
    """Сравнивает два словаря"""
    changed = False
    # Проверяем новые или измененные поля
    for f in user:
        if f not in old_user or old_user[f] != user[f]:
            changed = True
            break
    fields_to_delete = []
    # Првоеряем удаленные поля
    for f in old_user:
        if f not in user:
            fields_to_delete.append(f)
            changed = True
    if fields_to_delete:
        user['fields_to_delete'] = fields_to_delete
    return changed


def update_keyboard_to_user(user, keyboard_dict):
    """Обновляет или создает объект внутри пользователя для отправки клавиатуры"""
    print('Обновление клавиатуры пользователю', keyboard_dict)
    keyboard_to_user = user.get('keyboard_to_user', {})
    keyboard_to_user.update(keyboard_dict)
    user['keyboard_to_user'] = keyboard_to_user
    return False


def update_msg_to_user(user, msg_dict):
    """Обновляет или создает объект внутри пользователя для отправки клавиатуры"""
    print('Обновление сообщения пользователю', msg_dict)
    msg_to_user = user.get('msg_to_user', {})
    msg_to_user.update(msg_dict)
    user['msg_to_user'] = msg_to_user
