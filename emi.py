#!/usr/bin/env python3

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
from colorama import Fore, Style

warnings.filterwarnings("ignore")

# Define Google API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(message)
        sys.exit(2)

# Helper function to ensure positive integers are used for email counts
def positive_int(value):
    try:
        ivalue = int(value)
        if ivalue <= 0:
            raise argparse.ArgumentTypeError(f"{value} is invalid. Please specify a positive number of emails to read or leave empty.")
        return ivalue
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value} is invalid. Please specify a positive number of emails to read or leave empty.")

# Function to create an email message
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

# Function to send an email message
def send_message(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print(f"{datetime.now()} - sent")    
        bus = SessionBus()
        notifications = bus.get("org.freedesktop.Notifications")
        notifications.Notify(
            "My-Gmail",
            0,
            "",
            "My-Gmail",
            "Email sent",
            [],
            {},
            -1,
        )     
        return message
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to send an email
def send_email(service, to):
    from_email = "your_email@gmail.com"
    subject = input("Enter the email subject: ")
    message_text = input("Enter the email message: ")
    message = create_message(from_email, to, subject, message_text)
    send_message(service, 'me', message)

# Function to read emails from the user's account
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
                time.sleep(3)
        else:
            continue

        email_data = msg['payload']['headers']
        from_name = from_email = subject = date = text = ''
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
            if name == 'date':
                date = value

        print(f"{Style.BRIGHT}{Fore.YELLOW}From: {Style.RESET_ALL}{from_name} <{from_email}>")  # Yellow
        if date:
            print(f"{Style.BRIGHT}{Fore.CYAN}Date: {Style.RESET_ALL}{date}")  # Cyan
        if subject:
            print(f"{Style.BRIGHT}{Fore.LIGHTBLACK_EX}Subject: {Style.RESET_ALL}{subject}")  # Bright Black
        
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
            try:
                byte_code = base64.urlsafe_b64decode(data_text)
                text = byte_code.decode("utf-8")

                # If the content is HTML, parse it with BeautifulSoup
                soup = BeautifulSoup(text, "html.parser")
                text = soup.get_text()
                
                # Extract all hyperlinks from the HTML content and their corresponding text
                links = [(link.get('href'), " ".join(link.text.split())) for link in soup.find_all('a', href=True) if not link.get('href').startswith('mailto:')]
                
                # Remove leading and trailing whitespace and extra blank lines
                cleaned_text = "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())
            except (base64.binascii.Error, UnicodeDecodeError) as e:
                cleaned_text = "Failed to decode message content."
                links = []
        else:
            cleaned_text = "No message content found."
            links = []

        print(f"{Style.BRIGHT}{Fore.RED}Message: {Style.RESET_ALL}{cleaned_text}")  # Red
        
        # Print out any links found in the message with their corresponding text
        if links:
            print(f"{Style.BRIGHT}{Fore.MAGENTA}Links: {Style.RESET_ALL}")  # Magenta
            for link, link_text in links:
                if link_text:
                    print(f"{Style.BRIGHT}{Fore.GREEN}{link_text}{Style.RESET_ALL}: {link}")  # Green for link text
                else:
                    print(f"{link}")

# Argument parsing setup
parser = CustomArgumentParser(description='Read and send emails using Gmail API.')
parser.add_argument('-r', '--read', nargs='?', const=2, type=positive_int, help='Read the specified number of emails (default is 2 if no number is given).')
parser.add_argument('-s', '--send', metavar='email', type=str, help='Send an email to the specified address.')

# Display help if no arguments are provided
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit()

args = parser.parse_args()

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
        read_emails(service, args.read)
    elif args.send:
        if re.match(r"[^@]+@[^@]+\.[^@]+", args.send):
            send_email(service, args.send)
        else:
            print('Please provide a valid email address with the -s option.')

if __name__ == '__main__':
    main()
