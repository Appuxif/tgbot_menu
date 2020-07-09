# Дополнительный модуль для бота. 
# Функционал для различных операций с базой данных mongoDB
import os
import ssl
from urllib.parse import quote_plus as quote
from pymongo import MongoClient
from bson.json_util import dumps

# Ссылка на монгоБД

url = os.environ.get('MONGODB_URI')
if url:
    db_name = url.rsplit('/', 1)[1]
    # Объект базы данных монгоБД
    db = MongoClient(url, connect=False, retryWrites=False)[db_name]
else:
    users = {}

    class DB:
        def __init__(self):
            self.users = self.Users()

        class Users:
            def insert_one(self, user):
                users[user['_id']] = user

            def find_one(self, filtr):
                return users.get(filtr['_id'])

            def update_one(self, filtr, fields, upsert=False):
                user = users.get(filtr['_id'])
                if user:
                    user.update(fields)
                elif upsert:
                    filtr.update(fields)
                    self.insert_one(filtr)

            def delete_one(self, filtr):
                if filtr['_id'] in users:
                    users.pop(filtr['_id'])
    db = DB()

