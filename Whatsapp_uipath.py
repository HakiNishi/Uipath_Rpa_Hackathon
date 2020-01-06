import json
import requests
import base64
from twilio.twiml.messaging_response import MessagingResponse

def lambda_handler(event, context):
    
    encoded_body = event['body']
    decode_body = base64.b64decode(event['body']).decode('utf-8').split("&")
    msg = decode_body[4].split("=")[1]
    
    resp = MessagingResponse()
    resp.message("You said: {}".format(msg))
    
    print("hi")
    return str(resp)