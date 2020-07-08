# Дополнительный модуль для бота. 
# Функционал для различных операций с базой данных mongoDB
import os
import ssl
from urllib.parse import quote_plus as quote
from pymongo import MongoClient
from bson.json_util import dumps

# Ссылка на монгоБД

url = os.environ.get('MONGODB_URI')
db_name = url.rsplit('/', 1)[1]
# Объект базы данных монгоБД
db = MongoClient(url, connect=False)[db_name]
