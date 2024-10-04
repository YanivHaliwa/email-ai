from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import base64
import pickle
import sys
import os
import openai
from openai import OpenAI
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
from colorama import Fore, Style
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from pydbus import SessionBus
import os

#you can put this file in crontab to be sent recursively at a certain time


client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
openai.api_key = os.getenv("OPENAI_API_KEY")
modelSource = "gpt-4o"

CHUNK_SIZE = 1024  # Chunk size (you can adjust this as needed)

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']



def get_bot_response():
    user_input = "this email i send to my worker every day. write something nice to them"
    response = client.chat.completions.create(
    model=modelSource,
    messages=[
                {
                    'role': 'system',
                    'content': f'''
                  
                    '''
                },
               
                {
                    "role": "user",
                    "content": user_input
                },
        
    ],
    stream=True,
    temperature=0.7,
    max_tokens=2000
    )
    summary=""
    ch=""
    
    for chunk in response:
        ch = chunk.choices[0]
        txt=ch.delta.content
        if txt:
            summary += txt
      
    return summary

def send_email(service, to):
    from_email = ""  # Replace with your email
    subject =  ""
    message_text = get_bot_response()
    message = create_message(from_email, to, subject, message_text)
    send_message(service, 'me', message)

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        return message
    except Exception as e:
        print('An error occurred: %s' % e)
        return None


def main():

    client_secrets_file = 'credentials.json'  # Replace with the actual path
    client_token_file = 'token.pickle'  # Replace with the actual path

    txtbot=get_bot_response()
    print(txtbot)
    sys.exit(1)
    creds = None
  
    if os.path.exists(client_token_file):
        with open(client_token_file, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            with open(client_secrets_file, "r") as json_file:
                flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES)
                creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(client_token_file, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    send_email(service, "PUT EMAIL HERE")

    print(f"{datetime.now()} - sent") 

    bus = SessionBus()
    notifications = bus.get("org.freedesktop.Notifications")

    # Send a notification
    notifications.Notify(
        "Email-Auto",
        0,
        "",  # Icon path (empty for default)
        "Email-Auto",
        "Email sent to  ",
        [],  # Actions (empty for no actions)
        {},  # Hints
        -1,  # Expiration timeout
    )



if __name__ == '__main__':
    main()