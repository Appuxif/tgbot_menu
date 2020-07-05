#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import ssl
import traceback
import sys
from datetime import datetime
from aiohttp import web

import telebot

import utils.variables as vars
# from botmenu import bot, get_all
from botmenu import bot as botmenu
from bottour import bot as bottour
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
WEBHOOK_URL_PATH = f'/{botmenu.token}/'
WEBHOOK_URL_PATH2 = f'/{bottour.token}/'


app = web.Application()


# Process webhook calls
async def handle(request):
    bot = None
    if request.match_info.get('token') == botmenu.token:
        bot = botmenu
    elif request.match_info.get('token') == bottour.token:
        bot = bottour

    if bot is not None:
        request_body_dict = await request.json()
        update = telebot.types.Update.de_json(request_body_dict)
        bot.process_new_updates([update])
        return web.Response()
    else:
        return web.Response(text='Hello!')


async def control(request):
    print(request.query)
    if 'reload' in request.query:
        vars.update_variables()
        print('Гугл таблица загружена')
    return web.Response(text=str(request.query))


app.router.add_get('/control', control)
app.router.add_post('/{token}/', handle)

# Set webhook
botmenu.remove_webhook()
botmenu.set_webhook(
    url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
    # certificate=open(WEBHOOK_SSL_CERT, 'r')  # TODO: comment me on Heroku
)

bottour.remove_webhook()
bottour.set_webhook(
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

web.run_app(
    app,
    host=WEBHOOK_LISTEN,
    port=WEBHOOK_LISTEN_PORT,
    # ssl_context=context,
)
