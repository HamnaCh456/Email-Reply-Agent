from typing import List, Dict
import os  
import base64  
from google.auth.transport.requests import Request  
from google.oauth2.credentials import Credentials  
from google_auth_oauthlib.flow import InstalledAppFlow  
from googleapiclient.discovery import build  
from googleapiclient.errors import HttpError  
  
# Your existing functions (unchanged)  
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]  
  
def get_gmail_service():  
    """  
    Authenticates the user and returns a Gmail API service object.  
      
    This function handles the OAuth 2.0 flow for a desktop application.  
    It saves the credentials to 'token.json' after the first successful  
    authentication for future use.  
    """  
    creds = None  
    # The file token.json stores the user's access and refresh tokens.  
    if os.path.exists("token.json"):  
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)  
      
    # If there are no (valid) credentials available, let the user log in.  
    if not creds or not creds.valid:  
        if creds and creds.expired and creds.refresh_token:  
            # Refresh the token if it's expired  
            creds.refresh(Request())  
        else:  
            # Start the new authentication flow  
            flow = InstalledAppFlow.from_client_secrets_file(  
                "credentials.json", SCOPES  
            )  
            # This opens a browser window for you to log in  
            creds = flow.run_local_server(port=8000)  
          
        # Save the credentials for the next run  
        with open("token.json", "w") as token:  
            token.write(creds.to_json())  
  
    # Build and return the Gmail API service object  
    service = build("gmail", "v1", credentials=creds)  
    return service  
  
def get_message_body(message_part):  
    """  
    Decodes and returns the plain text body from a message part, removing email headers.  
  
    Args:  
        message_part: The 'payload' dictionary of a message or a message part.  
  
    Returns:  
        The decoded message body as a string with headers removed, or None if not found.  
    """  
    body = None
    
    # Check if the message has a body  
    if 'body' in message_part and 'data' in message_part['body']:  
        body = base64.urlsafe_b64decode(message_part['body']['data']).decode('utf-8')
      
    # If it's a multipart message, iterate through the parts  
    if body is None and 'parts' in message_part:  
        for part in message_part['parts']:  
            if part['mimeType'] == 'text/plain':  
                # Found the plain text part, return its decoded body  
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
    
    if body is None:
        return None
    
    # Clean up email headers: Remove lines like "On [Date] at [Time] [Sender] <email> wrote:"
    lines = body.split('\n')
    cleaned_lines = []
    skip_next_blank = False
    
    for line in lines:
        trimmed = line.strip()
        
        # Check if this is an email header line
        if trimmed.startswith('On ') and trimmed.endswith('wrote:'):
            skip_next_blank = True
            continue
        
        # Skip blank line immediately after header
        if skip_next_blank and trimmed == '':
            skip_next_blank = False
            continue
        
        skip_next_blank = False
        
        # Remove quoted lines (lines starting with >)
        if not trimmed.startswith('>'):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()  
  
def read_unread_threads(service):  
    """  
    Reads unread threads and returns a list of dictionaries.  
      
    Each dictionary contains the thread ID, subject, and the full conversation history.  
      
    Args:  
        service: Authorized Gmail API service instance.  
          
    Returns:  
        A list of dictionaries, where each dict has 'thread_id', 'subject', and 'history'.  
    """  
    print("Reading unread threads...")  
    unread_threads_data = []  
      
    try:  
        results = service.users().threads().list(userId='me', q='is:unread in:inbox -category:social -category:promotions -category:updates').execute()
        threads = results.get('threads', [])  
  
        if not threads:  
            print("No unread threads found in your inbox.")  
            return unread_threads_data  
  
        print("Unread threads found in your inbox:")  
        for thread in threads:  
            full_thread = service.users().threads().get(userId='me', id=thread['id']).execute()  
              
            first_message = full_thread['messages'][0]  
            headers = first_message['payload']['headers']  
            subject = 'No Subject'  
              
            for header in headers:  
                if header['name'] == 'Subject':  
                    subject = header['value']  
                    break  
              
            # Use a list to build the full conversation history.  
            full_conversation_history = []  
              
            # Iterate through all messages in the thread and get their body.  
            for message in full_thread['messages']:  
                body = get_message_body(message['payload'])  
                if body:  
                    full_conversation_history.append(body)  
              
            print("-" * 40)  
            print(f"--- Thread ID: {thread['id']} ---")  
            print(f"Subject: {subject}")  
            print("\nConversation History:\n" + "\n---\n".join(full_conversation_history))  
            print("-" * 40)  
              
            # Extract sender
            sender = 'Unknown'
            for header in headers:
                if header['name'] == 'From':
                    sender = header['value']
                    break
              
            # Append the structured data to the list.  
            unread_threads_data.append({  
                'thread_id': thread['id'],  
                'subject': subject,  
                'sender': sender,
                'history': "\n---\n".join(full_conversation_history)  
            })  
  
    except HttpError as error:  
        print(f"An error occurred while reading threads: {error}")  
      
    return unread_threads_data  
  
def fetch_unread_threads() -> str:  
    """  
    Reads unread Gmail threads and returns formatted conversation data.  
      
    Returns:  
        A formatted string with unread thread information including thread IDs,   
        subjects, and conversation history, or an error message if something goes wrong.  
    """  
    try:  
        service = get_gmail_service()  
        unread_threads_data = read_unread_threads(service)  
          
        if not unread_threads_data:  
            return "No unread threads found in your inbox."  
          
        # Format the data for the agent  
        formatted_output = []  
        for thread in unread_threads_data:  
            thread_info = f"Thread ID: {thread['thread_id']}\n"  
            thread_info += f"Subject: {thread['subject']}\n"  
            thread_info += f"Conversation:\n{thread['history']}\n"  
            thread_info += "-" * 40  
            formatted_output.append(thread_info)  
          
        return "\n\n".join(formatted_output)  
          
    except Exception as e:  
        return f"Error reading Gmail threads: {str(e)}"