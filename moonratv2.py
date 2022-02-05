"""
discord chat-bot Lambda handler.
"""

import os
import logging
import urllib
import configparser
import requests
import json

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# # Grab the Bot OAuth token from the environment.
PUBLIC_KEY = '36e021aad8da1ce202243153ca8ce6e71e544101281af49ee95ae22afc971ae3' # found on Discord Application -> General Information page
PING_PONG = {"type": 1}
RESPONSE_TYPES =  { 
                    "PONG": 1, 
                    "ACK_NO_SOURCE": 2, 
                    "MESSAGE_NO_SOURCE": 3, 
                    "MESSAGE_WITH_SOURCE": 4, 
                    "ACK_WITH_SOURCE": 5
                  }


def verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')
    
    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(auth_sig)) # raises an error if unequal

def ping_pong(body):
    if body.get("type") == 1:
        return True
    return False
    
def lambda_handler(event, context):
    print(f"event {event}") # debug print
    # verify the signature
    try:
        verify_signature(event)
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")


    # check if message is a ping
    body = event.get('body-json')
    if ping_pong(body):
        return PING_PONG
    
    # formatted_output = parse_crypto_commands(text, COINMARKETCAP_TOKEN)
    # # dummy return
    # return {
    #         "type": RESPONSE_TYPES['MESSAGE_NO_SOURCE'],
    #         "data": {
    #             "tts": False,
    #             "content": formatted_output,
    #             "embeds": [],
    #             "allowed_mentions": []
    #         }
    #     }

def parse_crypto_commands(text, api_token):
    '''
        Parses the string for known commands
    '''
    string = text.split()
    if '!price' == string[0]:
        crypto_db=create_crypto_db(api_token)
        try:
            req = requests.get(url='http://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol='+crypto_db[string[1].lower()],headers={'X-CMC_PRO_API_KEY':api_token},verify=False)
            return(create_coin_output(req.json()['data'][crypto_db[string[1].lower()]]))
        except IndexError:
            return('No coin mentioned...') 
    else:
        return("None")

def create_crypto_db(api_token):
    '''
        Create the database mapping's needed to make api requests to coinmarketcap.
    '''
    headers = {'X-CMC_PRO_API_KEY':api_token}

    req = requests.get(url='http://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit=5000', headers=headers, verify=False)
    all_coins = req.json()
    crypto_db = {}
    for data in all_coins['data']:
        all_coins[data['slug']] = data['symbol'].upper()
        all_coins[data['symbol'].lower()] = data['symbol'].upper()
    return all_coins

def create_coin_output(coin):
    '''
    create_coin_output gets the coin information for the specified coin
    and forms a string that will be sent into the slack api.
    '''
    coin_output1 = "Grabbing latest data for *" + coin['name'] + "*\n"
    coin_output2 = "```{:20s}\t${:.2f}\n".format("Price USD",float(coin['quote']['USD']['price']))
    coin_output3 = "{:20s}\t${:.2f}\n".format("Market Cap",float(coin['quote']['USD']['market_cap']))
    coin_output4 = "{:20s}\t{:.2f}%\n".format("Change 1hr",float(coin['quote']['USD']['percent_change_1h']))
    coin_output5 = "{:20s}\t{:.2f}%\n".format("Change 24hr",float(coin['quote']['USD']['percent_change_24h']))
    coin_output6 = "{:20s}\t{:.2f}%\n```".format("Change 7d",float(coin['quote']['USD']['percent_change_7d']))
    return (coin_output1+coin_output2+coin_output3+coin_output4+coin_output5+coin_output6)


