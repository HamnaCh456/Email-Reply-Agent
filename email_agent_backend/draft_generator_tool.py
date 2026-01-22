from email.message import EmailMessage
from typing import List, Dict
import base64
from googleapiclient.errors import HttpError
from email_fetcher_tool import get_gmail_service

def create_drafts_from_responses(thread_responses: List[Dict[str, str]]) -> str:
    """
    Creates draft replies for Gmail threads from response data and marks the original threads as read.
      
    Args:
        thread_responses: List of dictionaries with 'thread_id' and 'response' keys
          
    Returns:
        Status message indicating success or failure of draft creation and marking as read
    """
    try:
        service = get_gmail_service()
          
        if not thread_responses:
            return "No thread responses provided to create drafts for."

        results = []
        created_count = 0
          
        for thread_response in thread_responses:
            try:
                thread_id = thread_response['thread_id']
                response_content = thread_response['response']
                  
                # Get the original thread to extract recipient and subject
                full_thread = service.users().threads().get(userId='me', id=thread_id).execute()
                first_message = full_thread['messages'][0]
                headers = first_message['payload']['headers']
                  
                to_address = 'unknown'
                subject = 'No Subject'
                  
                for header in headers:
                    if header['name'] == 'From':
                        to_address = header['value']
                    elif header['name'] == 'Subject':
                        subject = header['value']

                # Create a draft
                message = EmailMessage()
                message.set_content(response_content)
                message["To"] = to_address
                message["Subject"] = f"Re: {subject}"
                  
                encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                  
                create_message = {
                    "message": {
                        "raw": encoded_message,
                        "threadId": thread_id
                    }
                }
                  
                draft = service.users().drafts().create(userId="me", body=create_message).execute()
                  
                # Mark the original email/thread as read
                service.users().threads().modify(
                    userId='me',
                    id=thread_id,
                    body={'removeLabelIds': ['UNREAD']}
                ).execute()
                  
                results.append(f"Draft created and thread marked as read for thread ID: {draft['message']['threadId']}")
                created_count += 1
            
            except HttpError as sub_error:
                results.append(f"Gmail API error occurred for thread ID {thread_id}: {sub_error}. Skipping this thread.")
            except KeyError as key_error:
                results.append(f"Missing key in thread response: {key_error}. Skipping this entry.")
            except Exception as sub_e:
                results.append(f"An unexpected error occurred for thread ID {thread_id}: {sub_e}. Skipping this thread.")
          
        summary = f"Successfully created {created_count} draft replies and marked corresponding emails as read.\n" + "\n".join(results)
        return summary
          
    except HttpError as error:
        return f"Gmail API error occurred while initializing the service: {error}"
    except Exception as e:
        return f"An unhandled error occurred: {str(e)}"
