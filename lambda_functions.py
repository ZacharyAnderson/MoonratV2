import json
from botocore.vendored import requests

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

AV_KEY = 'LF81812IX59K1B17'
PUBLIC_KEY = '<your public key here>' # found on Discord Application -> General Information page
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
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')
    
    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(auth_sig)) # raises an error if unequal

def ping_pong(body):
    return body.get("type") == 1

def crypto_price_check(body):
    return body.get("type") == 1 and body.get("type") == 'crypto'

def stock_price_check(body):
    return body.get("type") == 1 and body.get("type") == 'stock'

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

# print(fetch_crypto_price("BTC"))
# print(fetch_stock_price("TSLA")['05. price'])