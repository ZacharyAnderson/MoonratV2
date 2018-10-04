from moonratv2 import lambda_handler
import requests
import configparser
import os

def main():

    input = "!price tron" #you can get this from wherever, the command line, or read from a file or just leave as a constant
    data = { 'event': { 'text': input, 'channel': 'G9P7X8Q0H' }, 'local':True}
    lambda_handler(data,{})


if __name__ == "__main__":
    main()