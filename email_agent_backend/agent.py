from google import genai
from google.genai import types
import time
import os
from dotenv import load_dotenv

load_dotenv()

class RAGAgent:
    def __init__(self, file_path, store_name="NexaLearnStore", model_name=None):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")
        
        self.client = genai.Client(api_key=api_key)
        self.file_path = file_path
        self.store_name = store_name
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        print(f"RAGAgent initialized with model: {self.model_name}")
        self.store = None
        self._initialize_knowledge_base()

    def _initialize_knowledge_base(self):
        print("Initializing RAG Knowledge Base...")
        
        # Create a new store
        # Note: In a production environment, you might want to check if a store with this name already exists 
        # and reuse it to avoid creating duplicates. For now, we create one per process.
        self.store = self.client.file_search_stores.create(
            config={'display_name': self.store_name}
        )
        
        # Upload file
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Knowledge base file not found: {self.file_path}")

        # Explicitly upload the file first with mime_type
        print(f"Uploading file: {self.file_path}")
        file_upload = self.client.files.upload(
            file=self.file_path,
            config={
                'mime_type': 'text/plain',
                'display_name': os.path.basename(self.file_path)
            }
        )

        print(f"File uploaded: {file_upload.name}, adding to store...")      
        operation = self.client.file_search_stores.upload_to_file_search_store(
            file=self.file_path, 
            file_search_store_name=self.store.name,
            config={
                'display_name': os.path.basename(self.file_path),
                'mime_type': 'text/plain'
            }
        )
            
        # Wait for processing
        while not operation.done:
            print("Waiting for file processing...")
            time.sleep(2)
            operation = self.client.operations.get(operation=operation)
        
        print(f"RAG Knowledge Base Ready: {self.store.name}")

    def call(self, messages):
        """
        Generates a response using the RAG knowledge base.
        args:
            messages: A list of dicts [{'role': 'user', 'content': '...'}, ...]
        """
        # Extract the user prompt. 
        # If it's a list (as expected from main.py), take the last message content.
        if isinstance(messages, list):
            user_prompt = messages[-1].get('content', '')
        else:
            user_prompt = str(messages)

        print(f"Calling RAG with file search store: {self.store.name}")
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[self.store.name]
                        )
                    )
                ]
            )
        )
        
        print(f"RAG Response received: {response.text[:100] if response.text else 'No response'}")
        return response.text

current_dir = os.path.dirname(os.path.abspath(__file__))
nexa_file_path = os.path.join(current_dir, "nexa_learn.txt")

try:
    rag_llm = RAGAgent(file_path=nexa_file_path)
except Exception as e:
    print(f"Failed to initialize RAG Agent: {e}")
    rag_llm = None
