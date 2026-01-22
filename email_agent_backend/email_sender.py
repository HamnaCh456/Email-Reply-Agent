from email_fetcher_tool import get_gmail_service
from googleapiclient.errors import HttpError

def send_draft(draft_id):
    """
    Sends a Gmail draft by its ID.
    """
    try:
        service = get_gmail_service()
        sent_message = service.users().drafts().send(userId='me', body={'id': draft_id}).execute()
        return f"Successfully sent draft with ID: {draft_id}"
    except HttpError as error:
        return f"Gmail API error occurred: {error}"
    except Exception as e:
        return f"An unhandled error occurred: {str(e)}"

def send_draft_by_thread_id(thread_id):
    """
    Finds and sends the draft associated with a specific thread ID.
    """
    try:
        service = get_gmail_service()
        # List drafts in the specified thread
        drafts_response = service.users().drafts().list(userId='me', q=f'threadId:{thread_id}').execute()
        drafts = drafts_response.get('drafts', [])
        
        if not drafts:
            return f"No draft found for thread ID: {thread_id}"
        
        # In this workflow, we assume the most recent draft in the thread is the one to send
        draft_id = drafts[0]['id']
        service.users().drafts().send(userId='me', body={'id': draft_id}).execute()
        return f"Successfully sent draft for thread ID: {thread_id}"
        
    except HttpError as error:
        return f"Gmail API error occurred: {error}"
    except Exception as e:
        return f"An unhandled error occurred: {str(e)}"

def send_message(thread_id, response_content, to_address, subject):
    """
    Sends a new email message (alternative to sending a draft).
    """
    import base64
    from email.message import EmailMessage
    
    try:
        service = get_gmail_service()
        
        message = EmailMessage()
        message.set_content(response_content)
        message["To"] = to_address
        message["Subject"] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        send_message_body = {
            "raw": encoded_message,
            "threadId": thread_id
        }
        
        sent_message = service.users().messages().send(userId="me", body=send_message_body).execute()
        return f"Successfully sent email for thread ID: {thread_id}"
    except HttpError as error:
        return f"Gmail API error occurred: {error}"
    except Exception as e:
        return f"An unhandled error occurred: {str(e)}"
