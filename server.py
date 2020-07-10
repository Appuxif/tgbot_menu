#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import asyncio
# import ssl
# import traceback
# import sys
# from datetime import datetime
import threading
from time import sleep

import requests
from aiohttp import web

import telebot

import utils.variables as variables
# from botmenu import bot, get_all
import botmenu
import bottour
# from botmenu import bot as botmenu
# from bottour import bot as bottour
from config import (
    WEBHOOK_HOST,
    WEBHOOK_PORT,
    WEBHOOK_LISTEN,
    WEBHOOK_LISTEN_PORT,
    # WEBHOOK_SSL_CERT,
    # WEBHOOK_SSL_PRIV
)


# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = f'https://{WEBHOOK_HOST}:{WEBHOOK_PORT}'
WEBHOOK_URL_PATH = f'/{botmenu.bot.token}/'
WEBHOOK_URL_PATH2 = f'/{bottour.bot.token}/'


app = web.Application()


# Process webhook calls
async def handle(request):
    bot = None
    if request.match_info.get('token') == botmenu.bot.token:
        bot = botmenu.bot
    elif request.match_info.get('token') == bottour.bot.token:
        bot = bottour.bot

    if bot is not None:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        try:
            bot.process_new_updates([update])
        except Exception as err:
            bot.send_message(432134928, 'Ошибка: ' + str(err))
        return web.Response()
    else:
        return web.Response(text='Hello!')


async def control(request):
    print(request.query)
    if 'reload' in request.query:
        variables.update_variables()
        botmenu.update_variables()
        # bottour.reg.update_variables()
        print('Гугл таблица загружена')
    return web.Response(text=str(request.query))


# async def test(request):
#     print(request.query)
#     return web.


app.router.add_get('/control', control)
# app.router.add_get('/test', test)
app.router.add_post('/{token}/', handle)
app.router.add_static('/test', 'static')

# Set webhook
botmenu.bot.remove_webhook()
botmenu.bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    # certificate=open(WEBHOOK_SSL_CERT, 'r')  # TODO: comment me on Heroku
)

bottour.bot.remove_webhook()
bottour.bot.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH2,
    # certificate=open(WEBHOOK_SSL_CERT, 'r')  # TODO: comment me on Heroku
)

# Build ssl context
# context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
# context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)


# Start aiohttp server
# async def startHTTP():
#     runner = web.AppRunner(app)
#     await runner.setup()
#     site = web.TCPSite(runner, WEBHOOK_LISTEN, WEBHOOK_PORT)
#     await site.start()
# loop = asyncio.get_event_loop()
# loop.run_until_complete(startHTTP())
def server_no_sleep():
    """Время от времени делает запрос на сервер, чтобы он не уснул - heroku"""
    while True:
        requests.get(WEBHOOK_URL_BASE)
        sleep(600)


threading.Thread(target=server_no_sleep, daemon=True).start()


web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_LISTEN_PORT,
    # ssl_context=context,
)
