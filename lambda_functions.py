import json
import pprint

from botocore.vendored import requests

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

AV_KEY = 'LF81812IX59K1B17'
PUBLIC_KEY = '36e021aad8da1ce202243153ca8ce6e71e544101281af49ee95ae22afc971ae3' # found on Discord Application -> General Information page
PING_PONG = {"type": 1}
RESPONSE_TYPES =  { 
                    "PONG": 1, 
                    "ACK_NO_SOURCE": 2, 
                    "MESSAGE_NO_SOURCE": 3, 
                    "MESSAGE_WITH_SOURCE": 4, 
                    "ACK_WITH_SOURCE": 5
                  }
COINGECKO_BASEURL = 'https://api.coingecko.com/api/v3'
ALPHAVANTAGE_BASEURL = 'https://www.alphavantage.co'

def disc_format(content):
    print(content)
    return {
        "type": RESPONSE_TYPES['MESSAGE_NO_SOURCE'],
        "data": {
            "tts": False,
            "content": content,
            "embeds": [],
            "allowed_mentions": []
        }
    }


def fetch_coingecko_ids_list():
    req = requests.get(url=COINGECKO_BASEURL+'/coins/list')
    # pythonic as hell
    return dict([(x['symbol'], x['id']) for x in req.json()])

def format_price_response(symbol, price, change):
    modifier = "+"
    changeVal = float(change.strip('%'))
    if(changeVal < 0):
        modifier = ""
    return symbol.upper() + " " + "${:,.2f}".format(float(price)) + " " + modifier + "{:,.2f}".format(changeVal)+"% last 24h"

def fetch_crypto_price(symbol):
    if symbol == None or symbol == '':
        return disc_format("No ticker provided")

    idList = fetch_coingecko_ids_list()
    val = idList.get(symbol.lower())
    if (val == None):
        return disc_format("No coin found for " + symbol)

    req = requests.get(url=COINGECKO_BASEURL+'/coins/'+val+'?tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false')
    resp = req.json()
    if resp == None: 
        return disc_format("No data available for coin " + symbol)
    
    price = resp.get('market_data').get('current_price').get('usd')
    change = resp.get('market_data').get('price_change_percentage_24h')

    if price == None:
        return disc_format("No data available for coin " + symbol)

    return disc_format(format_price_response(symbol, str(price), str(change)+"%"))
    

def fetch_stock_price(symbol):
    if symbol == None or symbol == '':
        return disc_format("No ticker provided")

    req = requests.get(url=ALPHAVANTAGE_BASEURL+'/query?function=GLOBAL_QUOTE&symbol='+symbol+'&interval=5min&apikey='+AV_KEY)
    price = req.json().get('Global Quote').get('05. price')
    change = req.json().get('Global Quote').get('10. change percent')

    if price == None:
        return disc_format("No data available for ticker " + symbol)

    return disc_format(format_price_response(symbol, price, change))



def verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')

    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(auth_sig)) # raises an error if unequal

def ping_pong(body):
    return body.get("type") == 1 and body.get("data")['name'] == 'blep'

def crypto_price_check(body):
    return body.get("type") == 2 and body.get("data")['name'] == 'crypto'

def stock_price_check(body):
    return body.get("type") == 2 and body.get("data")['name'] == 'stock'

def lambda_handler(event, context):
    # verify the signature
    try:
        verify_signature(event)
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")

    # check if message is a ping
    body = event.get('body-json')
    if ping_pong(body):
        return PING_PONG

    if crypto_price_check(body):
        slug = body['data']['options'][0]['value']
        return fetch_crypto_price(slug)
    
    if stock_price_check(body):
        slug = body['data']['options'][0]['value']
        return fetch_stock_price(slug)
    
    
    return {
            "type": RESPONSE_TYPES['MESSAGE_NO_SOURCE'],
            "data": {
                "tts": False,
                "content": "BEEP BOOP",
                "embeds": [],
                "allowed_mentions": []
            }
    }

# test cases
# e1 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'crypto', 'options': [{'name': 'slug', 'type': 3, 'value': 'BTC'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# e2 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'stock', 'options': [{'name': 'slug', 'type': 3, 'value': 'AMZN'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# lambda_handler(e1, e1)
# lambda_handler(e2, e2)

# e3 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'crypto', 'options': [{'name': 'slug', 'type': 3, 'value': 'btc'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# e4 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'stock', 'options': [{'name': 'slug', 'type': 3, 'value': 'amzn'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# lambda_handler(e3, e3)
# lambda_handler(e4, e4)

# e5 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'crypto', 'options': [{'name': 'slug', 'type': 3, 'value': 'asdf'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# e6 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'stock', 'options': [{'name': 'slug', 'type': 3, 'value': 'afad'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# lambda_handler(e5, e5)
# lambda_handler(e6, e6)

# e7 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'crypto', 'options': [{'name': 'slug', 'type': 3, 'value': ''}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# e8 = {'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939649616092229712', 'name': 'stock', 'options': [{'name': 'slug', 'type': 3, 'value': ''}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939649678767685662', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NjQ5Njc4NzY3Njg1NjYyOlVQUzBES2F4WEc4SDZJT0pkSTBma1ozcE41ZFZIVzR6TE5TbzJkUVRUcEFVRTdHc0tMeHo3aVNSY3pPMjFxbUxIandQTmx5bHlWSzhOT09IVXFRYTNUWENLaUNLOExBcmdzd0FnRFpUekg2YjlOTDZRbm1WVXBqSzRrWmVKWmVS', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61fefaf5-206ba94f4570bf0d34db53f7', 'X-Forwarded-For': '35.196.132.85', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'c235ef865d0d2a2e0c93c31053698a6af8efd9498ce66655d029f61016526ae37cdd7ec20b5dba375fb618533cfc6abd8a0ba60801b6cba7c7b47bf2780f6d0f', 'x-signature-timestamp': '1644100341'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.196.132.85', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '0879b4f3-06c6-4f39-84dd-17236b53bdf0', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# lambda_handler(e7, e7)
# lambda_handler(e8, e8)