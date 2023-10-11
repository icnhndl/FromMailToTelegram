import base64
import os
import os.path
import traceback
from datetime import datetime
from time import sleep
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pyrogram import Client

CHECK_INTERVAL = 15
CREDENTIALS_PATH = 'credentials.json'
TOKEN_PATH = 'token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
ME_ID = 'me'
SENDER = 'Учебный отдел МКП'
TARGET_CHAT_ID = -1001735135708
API_HASH = '63254355bbdead1ada76fc74cc6904a1'
API_ID = 9411408


def save_date_to_pickle(data):
        with open('data.pickle', 'wb') as f:
            pickle.dump(data, f)



def get_date_from_pickle():
    try:
        with open('data.pickle', 'rb') as f:
            return pickle.load(f)
    except EOFError:
        return str(None)


def create_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service


def get_message_text(service, message):
    msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
    text = ''

    if 'parts' in msg['payload']:
        for part in msg['payload']['parts']:
            mime_type = part.get('mimeType')

            if mime_type == 'text/plain':
                data = part['body'].get('data')
                if data:
                    text += base64.urlsafe_b64decode(data).decode()

            elif mime_type == 'multipart/alternative':
                for sub_part in part['parts']:
                    sub_mime_type = sub_part.get('mimeType')

                    if sub_mime_type == 'text/plain':
                        data = sub_part['body'].get('data')
                        if data:
                            text += base64.urlsafe_b64decode(data).decode()

            elif mime_type == 'multipart/mixed':
                text += get_message_text(service, part)

    elif 'body' in msg['payload']:
        mime_type = msg['payload'].get('mimeType')

        if mime_type == 'text/plain':
            data = msg['payload']['body'].get('data')
            if data:
                text += base64.urlsafe_b64decode(data).decode()

    return text


def send_and_pin_message(text):
    message = client.send_message(TARGET_CHAT_ID, text)
    message.pin()


def format_schedule_text(text):
    return '\n'.join(text.split('\n')[1:-2])


def check_mail(service):
    query = f'from:{SENDER}'
    response = service.users().messages().list(userId=ME_ID, q=query).execute()

    if 'messages' in response:
        current_message = response['messages'][0]
        msg = service.users().messages().get(userId='me', id=current_message['id'], format='full').execute()
        message_date = msg['internalDate']
        last_message_date = get_date_from_pickle()
        if last_message_date != message_date:
            save_date_to_pickle(message_date)
            text = get_message_text(service, current_message)
            formated_text = format_schedule_text(text)
            print(f'[{datetime.today()}] Message sent successfully')
            send_and_pin_message(formated_text)
        else:
            print(f'[{datetime.today()}] There is no new messages from {SENDER}')
    else:
        print(f'[{datetime.today()}] There is no any messages from {SENDER}')


def main():
    service = create_service()
    while True:
        try:
            check_mail(service)
            sleep(CHECK_INTERVAL)
        except:
            print(f'[{datetime.today()}] ! EXEPTION COUGHT !')
            print(traceback.print_exc())


client = Client('FromMailToTelegram', API_ID, API_HASH)
client.start()
main()
client.stop()
