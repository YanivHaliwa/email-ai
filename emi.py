from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import os.path
import base64
import re
import pickle
import argparse
import sys
from pydbus import SessionBus
from datetime import datetime
from urllib.parse import urlparse
from hyperlink import URL
import warnings
from google.auth.exceptions import RefreshError
import requests
from requests.adapters import HTTPAdapter
import ssl 
import time
import ssl
import google.auth.exceptions


warnings.filterwarnings("ignore")


# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']


class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(message)
        #self.print_help()
        sys.exit(2)

def positive_int(value):
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid. Please specify the number of emails to read or leave empty")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is an invalid. Please specify the number of emails to read or leave empty")


# Create the parser
#parser = argparse.ArgumentParser(description='Read or send emails.')
parser = CustomArgumentParser(description='Read-send emails.')

# Add the arguments
# group = parser.add_mutually_exclusive_group(required=True)
parser.add_argument('-r', '--read', nargs='?', const=2, type=positive_int, help='Read emails')

# try:
#     args = parser.parse_args()
# except SystemExit:
#     sys.exit()

parser.add_argument('-s', '--send', metavar='email', type=str, help='Send an email')


if len(sys.argv)==1:
    print('Please specify an option: -r to read emails, -s followed by an email address to send an email.')
    sys.exit()

# Parse the arguments
args = parser.parse_args()


def send_email(service, to):
    from_email = "your_email@gmail.com"  # Replace with your email
    subject = input("Enter the email subject: ")
    message_text = input("Enter the email message: ")
    message = create_message(from_email, to, subject, message_text)
    send_message(service, 'me', message)


def create_message(sender, to, subject, message_text):
    """Create a message for an email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
 
def send_message(service, user_id, message):
    """Send an email message."""
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print(f"{datetime.now()} - sent")    
        bus = SessionBus()
        notifications = bus.get("org.freedesktop.Notifications")

        # Send a notification
        notifications.Notify(
            "My-Gmail",
            0,
            "",  # Icon path (empty for default)
            "My-Gmail",
            "Email sent",
            [],  # Actions (empty for no actions)
            {},  # Hints
            -1,  # Expiration timeout
        )     
        return message
    except Exception as e:
        print('An error occurred: %s' % e)
        return None

def read_emails(service, num_emails):
    try:
        results = service.users().messages().list(userId='me', maxResults=num_emails).execute()
        messages = results.get('messages', [])
    except Exception as e:
        print(f"Failed to list messages: {e}")
        return

    if not messages:
        print('No new messages.')
        return

    print('Messages:')
    for count, message in enumerate(messages):
        if count > 0:
            print('\n')

        retries = 3
        for attempt in range(retries):
            try:
                msg = service.users().messages().get(userId='me', id=message['id']).execute()
                break
            except (ssl.SSLError, google.auth.exceptions.RefreshError) as e:
                pass #print(f"Attempt {attempt + 1}/{retries} failed to fetch message: {e}")
                time.sleep(3)
        else:
            pass# print("Failed to fetch message after several attempts.")
            continue

        email_data = msg['payload']['headers']
        from_name = from_email = subject = text = ''
        for values in email_data:
            name = values['name'].lower()  # Convert the header name to lowercase
            value = values['value']
            if name == 'from':
                match = re.match(r'(.*)<(.*)>', value)
                if match:
                    from_name, from_email = match.groups()
                else:
                    from_name = value
                    from_email = ''
            if name == 'subject':
                subject = value

        print('\033[1m' + '\033[94m' + 'From: ' + '\033[0m' + from_name + ' <' + from_email + '>')  # Blue
        print('\033[1m' + '\033[33m' + 'Subject: ' + '\033[0m' + subject)  # Orange
        
        # Check for both text/plain and text/html parts in the 'parts' or sub-parts
        def get_data_text(parts):
            html_data_text = ""
            plain_data_text = ""
            for part in parts:
                mime_type = part['mimeType']
                if mime_type == 'text/html':
                    html_data_text = part['body']['data']
                elif mime_type == 'text/plain':
                    plain_data_text = part['body']['data']
                elif mime_type == 'multipart/alternative':
                    return get_data_text(part['parts'])

            return html_data_text if html_data_text else plain_data_text

        if 'parts' in msg['payload']:
            data_text = get_data_text(msg['payload']['parts'])
        else:
            data_text = msg['payload']['body'].get('data', '')

        if data_text:
            byte_code = base64.urlsafe_b64decode(data_text)
            text = byte_code.decode("utf-8")

            # If the content is HTML, parse it with BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text()

            # Remove leading and trailing whitespace and extra blank lines
            cleaned_text = "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())
        else:
            cleaned_text = "No message content found."

        print('\033[1m' + '\033[91m' + 'Message: ' + '\033[0m' + cleaned_text)  # Red

 
def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                # The refresh token is invalid or expired, need to re-authenticate
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
 
    if args.read:
    # Call the function to read emails
        read_emails(service, args.read)
    elif args.send is not False:
        # Check if an email address is provided
        if args.send:
            # Check if the email address is valid
            if re.match(r"[^@]+@[^@]+\.[^@]+", args.send):
                # Call the function to send an email
                send_email(service, args.send)
            else:
                print('Please provide a valid email address with the -s option.')
        else:
            print('Please use -s followed by an email address to send an email.')


if __name__ == '__main__':
    main()
 