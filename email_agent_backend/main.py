from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import time
from dotenv import load_dotenv

from email_fetcher_tool import fetch_unread_threads, get_gmail_service, read_unread_threads
from draft_generator_tool import create_drafts_from_responses
from email_sender import send_message
from agent import rag_llm as llm

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Detect frontend path
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dist_path = os.path.join(os.path.dirname(current_dir), "frontend", "dist")

class ThreadResponse(BaseModel):
    thread_id: str
    response: str

class EmailData(BaseModel):
    thread_id: str
    subject: str
    sender: str
    history: str

@app.get("/emails", response_model=List[EmailData])
async def get_emails():
    try:
        service = get_gmail_service()
        emails = read_unread_threads(service)
        return emails
    except Exception as e:
        print(f"Error fetching emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_draft")
async def generate_draft(email: EmailData):
    try:
        print(f"Generating draft for thread: {email.thread_id}")
        
        # Show generating draft message and wait for 2 seconds
        print("Generating Draft...")
        time.sleep(2)

        # Use RAG LLM for all questions with improved customer service prompt
        prompt = f"""You are a professional customer service agent for Nexa Learn. You have access to the company's knowledge base and services through a file search tool.

Your task: Respond to the following customer inquiry using ONLY the information from the company knowledge base provided via file search.

Customer Email:
Subject: {email.subject}
From: {email.sender}
Previous conversation history:
{email.history}

IMPORTANT INSTRUCTIONS:
1. SEARCH the knowledge base for relevant information about: resume reviews, interviews, placement support, career guidance, company programs, and services
2. USE specific details from the knowledge base in your response - include exact quotes or paraphrasing from the knowledge base
3. Reference specific programs, support mechanisms, and services mentioned in the knowledge base
4. Be professional, empathetic, and provide concrete information
5. Answer ONLY what the customer asked - don't add unnecessary information
6. If information is not in the knowledge base, acknowledge and suggest contacting support
7. Always maintain a professional tone and end with a call to action or helpful closing

Generate a professional response to the customer's last message using the knowledge base.
Return ONLY the reply text, no other formatting or explanations."""
        
        response = llm.call([{"role": "user", "content": prompt}])

        print(f"Draft generated: {response[:50]}...")
        return {"draft": response}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating draft: {error_details}")
        raise HTTPException(status_code=500, detail=str(e))

class SendEmailRequest(BaseModel):
    thread_id: str
    response: str
    recipient: str
    subject: str

@app.post("/send_email")
async def send_email_endpoint(data: SendEmailRequest):
    try:
        result = send_message(
            thread_id=data.thread_id,
            response_content=data.response,
            to_address=data.recipient,
            subject=f"Re: {data.subject}"
        )
        
        # Mark thread as read
        service = get_gmail_service()
        service.users().threads().modify(
            userId='me',
            id=data.thread_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        return {"status": "success", "message": result}
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send_draft")
async def send_draft(data: ThreadResponse):
    try:
        result = create_drafts_from_responses([{"thread_id": data.thread_id, "response": data.response}])
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (must be after API routes)
if os.path.exists(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_path = os.path.join(frontend_dist_path, "index.html")
        return FileResponse(index_path)
else:
    print(f"Warning: Frontend dist not found at {frontend_dist_path}. Run 'npm run build' in frontend directory.")

if __name__ == "__main__":
    import uvicorn
    # Use port 8001 to match user's previous requests and existing terminals
    uvicorn.run(app, host="0.0.0.0", port=8001)
