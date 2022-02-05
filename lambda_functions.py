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

def fetch_coingecko_ids_list():
    req = requests.get(url=COINGECKO_BASEURL+'/coins/list')
    # pythonic as hell
    return dict([(x['symbol'], x['id']) for x in req.json()])

def fetch_crypto_price(symbol):
    try:
        idList = fetch_coingecko_ids_list()
        val = idList[symbol.lower()]
        if (val == None):
            return
        req = requests.get(url=COINGECKO_BASEURL+'/simple/price?ids='+val+'&vs_currencies=usd')
        return req.json()[val]['usd']
    except IndexError:
        return('No coin mentioned...') 

def fetch_stock_price(symbol):
    req = requests.get(url=ALPHAVANTAGE_BASEURL+'/query?function=GLOBAL_QUOTE&symbol='+symbol+'&interval=5min&apikey='+AV_KEY)
    return req.json()['Global Quote']


def verify_signature(event):
    print('1')
    raw_body = event.get("rawBody")
    print('2')
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')
    print('3')
    print(auth_sig)
    print(auth_ts)
    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(auth_sig)) # raises an error if unequal

def ping_pong(body):
    return body.get("type") == 1 and body.get("name") == 'blep'

def crypto_price_check(body):
    return body.get("type") == 1 and body.get("name") == 'crypto'

def stock_price_check(body):
    return body.get("type") == 1 and body.get("name") == 'stock'

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
        return fetch_crypto_price("BTC")
    
    if stock_price_check(body):
        return fetch_crypto_price("TSLA")
    
    
    # dummy return
    return {
            "type": RESPONSE_TYPES['MESSAGE_NO_SOURCE'],
            "data": {
                "tts": False,
                "content": "BEEP BOOP",
                "embeds": [],
                "allowed_mentions": []
            }
    }

# pp = pprint.PrettyPrinter()
# c = {'rawBody': '{"application_id":"939347166797910087","channel_id":"939555183602589701","data":{"id":"939570178449104957","name":"blep","options":[{"name":"animal","type":3,"value":"animal_dog"}],"type":1},"guild_id":"939555183602589698","guild_locale":"en-US","id":"939573710749327410","locale":"en-US","member":{"avatar":null,"communication_disabled_until":null,"deaf":false,"is_pending":false,"joined_at":"2022-02-05T16:16:51.873000+00:00","mute":false,"nick":null,"pending":false,"permissions":"2199023255551","premium_since":null,"roles":[],"user":{"avatar":"acb266be9634141c764a158131964ddf","discriminator":"7196","id":"279414394922991616","public_flags":0,"username":"zachand"}},"token":"aW50ZXJhY3Rpb246OTM5NTczNzEwNzQ5MzI3NDEwOjFrSEdEUVJYN2UwUEVIYTFONDNOMWVsbnVIMWJkSEhJcWI1bGZUVWJ0SXpEeWx2cTluNTBjUU9WRlJ2aDA2N2M5SUlublB4YXQ4cFozbEZxbzYzdUJ4T3VTdHZLZVZBTlJsMm92ZXFLbUpoSzk0dVpWTjJ3YTgxVFFQZHNBMTRQ","type":2,"version":1}', 'body-json': {'application_id': '939347166797910087', 'channel_id': '939555183602589701', 'data': {'id': '939570178449104957', 'name': 'blep', 'options': [{'name': 'animal', 'type': 3, 'value': 'animal_dog'}], 'type': 1}, 'guild_id': '939555183602589698', 'guild_locale': 'en-US', 'id': '939573710749327410', 'locale': 'en-US', 'member': {'avatar': None, 'communication_disabled_until': None, 'deaf': False, 'is_pending': False, 'joined_at': '2022-02-05T16:16:51.873000+00:00', 'mute': False, 'nick': None, 'pending': False, 'permissions': '2199023255551', 'premium_since': None, 'roles': [], 'user': {'avatar': 'acb266be9634141c764a158131964ddf', 'discriminator': '7196', 'id': '279414394922991616', 'public_flags': 0, 'username': 'zachand'}}, 'token': 'aW50ZXJhY3Rpb246OTM5NTczNzEwNzQ5MzI3NDEwOjFrSEdEUVJYN2UwUEVIYTFONDNOMWVsbnVIMWJkSEhJcWI1bGZUVWJ0SXpEeWx2cTluNTBjUU9WRlJ2aDA2N2M5SUlublB4YXQ4cFozbEZxbzYzdUJ4T3VTdHZLZVZBTlJsMm92ZXFLbUpoSzk0dVpWTjJ3YTgxVFFQZHNBMTRQ', 'type': 2, 'version': 1}, 'params': {'path': {}, 'querystring': {}, 'header': {'content-type': 'application/json', 'Host': 'da7uq70ft7.execute-api.us-east-1.amazonaws.com', 'User-Agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'X-Amzn-Trace-Id': 'Root=1-61feb435-4f545f442c0e585022d36eca', 'X-Forwarded-For': '35.237.4.214', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https', 'x-signature-ed25519': 'cee187b42ca9bb900023cf41e8805127df270dbb22cf2c0bdd2590f85a6b30c1f51907bf606f6b03e3037615086cefd95633be362152a85bebe5fe8d10790905', 'x-signature-timestamp': '1644082229'}}, 'stage-variables': {}, 'context': {'account-id': '', 'api-id': 'da7uq70ft7', 'api-key': '', 'authorizer-principal-id': '', 'caller': '', 'cognito-authentication-provider': '', 'cognito-authentication-type': '', 'cognito-identity-id': '', 'cognito-identity-pool-id': '', 'http-method': 'POST', 'stage': 'biz', 'source-ip': '35.237.4.214', 'user': '', 'user-agent': 'Discord-Interactions/1.0 (+https://discord.com)', 'user-arn': '', 'request-id': '35b20fad-0ec2-4a7a-9181-95e1e934f40e', 'resource-id': 'lxqs55', 'resource-path': '/event'}}
# pp.pprint(verify_signature(c))
# print(fetch_crypto_price("BTC"))
# print(fetch_stock_price("TSLA")['05. price'])