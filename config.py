import os

sheet_api_url = os.environ.get('SHEET_API_URL')
sheet_api_url2 = os.environ.get('SHEET_API_URL2')
ya_money_url = os.environ.get('YA_MONEY_URL')
ya_money_url2 = os.environ.get('YA_MONEY_URL2')

token = os.environ.get('TOKEN', '856621453:AAHtVJEIMsD5WZH9ytescn16_dYZajyluL4')
token2 = os.environ.get('TOKEN2', '856621453:AAHtVJEIMsD5WZH9ytescn16_dYZajyluL4')

WEBHOOK_HOST = os.environ.get('HOST')
WEBHOOK_PORT = 443
WEBHOOK_LISTEN_PORT = os.environ.get('PORT', 8443)
WEBHOOK_LISTEN = '0.0.0.0'

# На хероку не нужно
# WEBHOOK_SSL_CERT = './webhook_cert.pem'
# WEBHOOK_SSL_PRIV = './webhook_pkey.pem'
