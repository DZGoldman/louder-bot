import os.path
import base64
import email
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timezone
from bs4 import BeautifulSoup
import time

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

WAIT_TIME = 5

def wait_and_retry_get_link_from_email(new_retries):
    print("Waiting and retrying get link from email:")
    if new_retries < 1:
        raise Exception("no more attempts left")
    time.sleep(WAIT_TIME)
    return get_link_from_email(new_retries)

def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if not os.path.exists('credentials.json'):
            raise Exception("Need to provide credentials.json")
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_link_from_email(retries = 5):
    if retries < 1:
        raise Exception("no more attempts left")
    creds = get_creds()
    # Call the Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # Fetch the list of emails
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])




    if not messages:
        print("No messages found")
        return wait_and_retry_get_link_from_email(retries -1)
    else:
        
        message = messages[0]
        # first message:
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        
        # Parse the email headers for the subject
        headers = msg['payload']['headers']

        date_str = next((header['value'] for header in headers if header['name'] == 'Date'), 'No Date')
        # Parse the date string to a datetime object
        date_sent = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        # Set timezone to UTC for the parsed date (since it's in GMT)
        date_sent = date_sent.replace(tzinfo=timezone.utc)
        # Get the current time in UTC
        current_time = datetime.now(timezone.utc)
        # Calculate the difference in seconds
        elapsed_time = (current_time - date_sent).total_seconds()

        elapsed_time_minutes_limit = 3
        if elapsed_time > 60 * elapsed_time_minutes_limit:
            print(f"Last email > {elapsed_time_minutes_limit} minutes old")
            return wait_and_retry_get_link_from_email(retries -1)


        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')

    
        if "Sign in to Udio" in subject:
            print("Login email found");
            # Parse the email body
            parts = msg['payload'].get('parts')
            if parts:
                for part in parts:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode()
                        # TODO: handle 
                    elif part['mimeType'] == 'text/html':
                        body_html = base64.urlsafe_b64decode(part['body']['data']).decode()
                        soup = BeautifulSoup(body_html, 'html.parser')
                        links = soup.find_all('a')
                        for link in links:
                            if "Sign in to Udio" in link.string:
                                print("Href found",link["href"])
                                return link["href"]

            else:
                # Handle cases where the body might be directly in payload
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode()
                # TODO: handle
        else:
            print("Unrecognized subject in latest email:", subject)
            return wait_and_retry_get_link_from_email(retries -1)


def test_messages():
    creds = get_creds()
    # Call the Gmail API
    service = build('gmail', 'v1', credentials=creds)

    # Fetch the list of emails
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = results.get('messages', [])
    if (len(messages) > 0):
        
        print(f"Auth successful 👍; {len(messages)} emails found")
    else:
        print("Auth succeeded, but not emails found; check inbox")
if __name__ == "__main__":
    test_messages()
    