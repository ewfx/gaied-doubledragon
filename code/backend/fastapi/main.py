from fastapi import FastAPI, UploadFile, Form, File, HTTPException, Query
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from openai import AsyncOpenAI
import os
import json
import PyPDF2
import docx
import pytesseract
from PIL import Image
from dotenv import load_dotenv
import io
import random
import string
from datetime import datetime
from bson import ObjectId, json_util
import tempfile
import shutil
import email
import email.policy
from email.parser import BytesParser
import mimetypes
import uuid

# Import the create_assistant_with_vector_store method from helper.py
from helper import create_assistant_with_vector_store

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
client_db = MongoClient(MONGO_URI)
db = client_db["dashboard"]
collection = db["emails"]

# Set the uploaded Assistant ID (Replace with actual ID after uploading)
ASSISTANT_ID = "asst_FS8ltK3lrQwZ4BmGQ5CtD7ZI"

# Create a temporary directory if it doesn't exist
TMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

# List of domain names for generating random email addresses
EMAIL_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "example.com",
    "loanservice.com",
    "mortgagehelp.net",
    "financialaid.org",
]


def generate_random_email():
    """Generate a random email address."""
    # Generate random username (5-10 characters)
    username_length = random.randint(5, 10)
    username = "".join(
        random.choices(string.ascii_lowercase + string.digits, k=username_length)
    )

    # Randomly decide if we want to add a period or underscore
    if random.random() > 0.7:
        separator = random.choice(["_", "."])
        second_part_length = random.randint(3, 7)
        second_part = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=second_part_length)
        )
        username = f"{username}{separator}{second_part}"

    # Select a random domain
    domain = random.choice(EMAIL_DOMAINS)

    return f"{username}@{domain}"


def extract_text_from_file(file: UploadFile) -> str:
    """Extracts text from supported file types."""
    print(file)
    content = file.file.read()
    file_type = file.filename.split(".")[-1].lower()
    if file_type == "pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n".join(
            [page.extract_text() for page in reader.pages if page.extract_text()]
        )
    elif file_type == "docx":
        doc = docx.Document(io.BytesIO(content))
        return "\n".join([p.text for p in doc.paragraphs])
    elif file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(io.BytesIO(content))
        return pytesseract.image_to_string(image)
    elif file_type == "txt":
        return content.decode("utf-8")
    elif file_type == "eml":
        # Parse the .eml file
        msg = BytesParser(policy=email.policy.default).parse(io.BytesIO(content))

        # Extract the email body
        email_body = ""

        # Get the plain text body
        if msg.get_body(preferencelist=("plain",)):
            email_body = msg.get_body(preferencelist=("plain",)).get_content()
        # If no plain text, try HTML
        elif msg.get_body(preferencelist=("html",)):
            # This is a simple approach - in production you might want to use
            # a proper HTML to text converter like html2text
            html_body = msg.get_body(preferencelist=("html",)).get_content()
            email_body = f"HTML Email: {html_body}"

        # Add headers information
        headers = f"From: {msg['from']}\nTo: {msg['to']}\nSubject: {msg['subject']}\nDate: {msg['date']}\n\n"

        return headers + email_body
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")


def extract_attachments_from_eml(eml_content):
    """
    Extracts attachments from an EML file.

    Args:
        eml_content (bytes): The content of the EML file

    Returns:
        list: A list of dictionaries containing attachment information
    """
    # Parse the email message
    msg = BytesParser(policy=email.policy.default).parse(io.BytesIO(eml_content))

    attachments = []

    # Iterate through all attachments
    for part in msg.iter_attachments():
        # Get the filename
        filename = part.get_filename()
        if not filename:
            # Generate a filename if none exists
            ext = mimetypes.guess_extension(part.get_content_type())
            filename = f"attachment-{uuid.uuid4()}{ext if ext else '.bin'}"

        # Get the content
        content = part.get_content()

        # Save the attachment to a temporary file
        temp_path = os.path.join(TMP_DIR, filename)

        # Handle binary content
        if isinstance(content, bytes):
            with open(temp_path, "wb") as f:
                f.write(content)
        else:
            # Handle text content
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

        attachments.append(
            {
                "filename": filename,
                "path": temp_path,
                "content_type": part.get_content_type(),
            }
        )

    return attachments


async def classify_email(email_body: str) -> dict:
    """Uses OpenAI Assistant to classify email request type and extract sub-request types with confidence scores."""

    prompt = (
        "You are an AI assistant that classifies loan servicing request emails. "
        "For the given email content, provide the top 3 most relevant request intents, along with reasoning and a confidence score (0-1) for each. "
        "Also, extract sub-request types (features) present in the email and justify why they are relevant. "
        "Use the provided dataset file for reference. Format the response as a JSON object with 'request_intents' "
        "containing a list of dictionaries (each with 'intent', 'reasoning', and 'confidence_score'), "
        "and 'sub_requests' containing a list of dictionaries (each with 'sub_request' and 'reasoning')."
        f"\n\nEmail Content:\n{email_body}"
    )

    # Create a thread to handle the classification
    thread_response = await client.beta.threads.create()
    thread_id = thread_response.id

    # Send the email text as a message in the thread
    await client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=prompt
    )

    # Run the assistant to process the request
    run_response = await client.beta.threads.runs.create(
        thread_id=thread_id, assistant_id=ASSISTANT_ID
    )

    # Wait for completion
    while run_response.status not in ["completed", "failed"]:
        run_response = await client.beta.threads.runs.retrieve(
            thread_id=thread_id, run_id=run_response.id
        )

    if run_response.status == "failed":
        raise HTTPException(
            status_code=500, detail="OpenAI Assistant failed to process request"
        )

    # Extract the response from the assistant
    messages = await client.beta.threads.messages.list(thread_id=thread_id)

    # Get the assistant's response (first message in the list)
    if messages.data and len(messages.data) > 0:
        # Get the first message (assistant's response)
        assistant_message = messages.data[0]

        if assistant_message.content and len(assistant_message.content) > 0:
            # Get the text content
            text_content = assistant_message.content[0].text.value

            # The JSON is often wrapped in a markdown code block, so we need to extract it
            if "" in text_content:
                # Extract the JSON part from the markdown code block
                json_text = text_content.split("json")[1].split("```")[0].strip()
            else:
                json_text = text_content

            try:
                return json.loads(json_text)  # Parse response JSON
            except json.JSONDecodeError as e:
                # If not valid JSON, return as text
                raise HTTPException(
                    status_code=500, detail=f"Invalid JSON in response: {str(e)}"
                )

    # Fallback if we can't extract proper response
    raise HTTPException(status_code=500, detail="Could not parse assistant response")


# Define a function to generate embeddings
async def get_embedding(text):
    """Generates vector embeddings for the given text."""
    embedding = await client.embeddings.create(
        input=[text], model="text-embedding-3-small"
    )
    return embedding.data[0].embedding


def store_email(email_data: dict):
    """Stores email in MongoDB."""
    collection.insert_one(email_data)


def search_similar_emails(query_embedding):
    """Performs a vector search in MongoDB for similar emails."""
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedding",
                "exact": True,
                "limit": 5,
            }
        },
        {
            "$project": {
                "_id": 0,
                "email": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    results = collection.aggregate(pipeline)
    return list(results)


def cleanup_temp_files(file_paths):
    """Cleans up temporary files."""
    for path in file_paths:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error removing temporary file {path}: {e}")


@app.post("/process_email")
async def process_email(
    email_body: Optional[str] = Form(None),
    email_file: Optional[UploadFile] = File(None),
    attachments: List[UploadFile] = File([]),
):
    """
    Processes an email, classifies it, extracts details, and checks for duplicates.

    Can handle:
    1. Plain text email body
    2. .eml file with embedded attachments
    3. .eml file with separate attachments
    4. Any combination of the above
    """
    print(email_body), print(email_file), print(attachments)
    temp_files = []  # Track temporary files for cleanup
    try:
        extracted_text = ""
        processed_attachments = []

        # Case 1: Process email body if provided
        if email_body:
            extracted_text = email_body

        # Case 2 & 3: Process .eml file if provided
        if email_file:
            # Read the email file content
            email_content = await email_file.read()

            # Extract text from the email file
            if email_file.filename.lower().endswith(".eml"):
                # Parse the email to get the body
                extracted_text += extract_text_from_file(email_file)

                # Extract embedded attachments from the .eml file
                embedded_attachments = extract_attachments_from_eml(email_content)
                temp_files.extend([att["path"] for att in embedded_attachments])

                # Process each embedded attachment
                for attachment in embedded_attachments:
                    # Create a temporary UploadFile-like object
                    with open(attachment["path"], "rb") as f:
                        content = f.read()

                    temp_upload_file = UploadFile(
                        filename=attachment["filename"], file=io.BytesIO(content)
                    )

                    # Try to extract text from the attachment
                    try:
                        attachment_text = extract_text_from_file(temp_upload_file)
                        extracted_text += f"\n\n[Attachment: {attachment['filename']}]\n{attachment_text}"
                        processed_attachments.append(attachment["filename"])
                    except HTTPException:
                        # If we can't extract text, just note the attachment
                        extracted_text += f"\n\n[Attachment: {attachment['filename']} - Could not extract text]"
                        processed_attachments.append(attachment["filename"])
            else:
                # For non-eml files, just extract the text
                extracted_text += extract_text_from_file(email_file)

        # Process additional attachments
        for attachment in attachments:
            try:
                attachment_text = extract_text_from_file(attachment)
                extracted_text += (
                    f"\n\n[Attachment: {attachment.filename}]\n{attachment_text}"
                )
                processed_attachments.append(attachment.filename)
            except HTTPException:
                # If we can't extract text, just note the attachment
                extracted_text += (
                    f"\n\n[Attachment: {attachment.filename} - Could not extract text]"
                )
                processed_attachments.append(attachment.filename)

        # If we have no content, raise an error
        if not extracted_text:
            raise HTTPException(status_code=400, detail="No email content provided")

        # Classify the email
        classification = await classify_email(extracted_text)
        embedded_email = await get_embedding(extracted_text)
        similar_emails = search_similar_emails(embedded_email)

        # Generate a random receiver email ID
        receiver_email = generate_random_email()

        # Add timestamp for when the email was processed
        timestamp = datetime.now()

        # Create the email data object
        email_data = {
            "email": extracted_text,
            "classification": classification,
            "similar_emails": similar_emails,
            "receiver_email": receiver_email,
            "created_at": timestamp,
            "attachments": processed_attachments,
            "embedding": embedded_email,
        }

        print(email_data)

        # Store the email in MongoDB
        store_email(email_data)

        # Return the response
        return {
            "classification": classification,
            "similar_emails": similar_emails,
            "receiver_email": receiver_email,
            "created_at": timestamp,
            "attachments": processed_attachments,
        }

    except Exception as e:
        print(f"Error processing email: {str(e)}")
        # Clean up temporary files in case of error
        cleanup_temp_files(temp_files)
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

    finally:
        # Always clean up temporary files
        cleanup_temp_files(temp_files)


@app.get("/database/collections")
async def get_collections():
    """Returns a list of all collections in the database."""
    try:
        collections = db.list_collection_names()
        return {"collections": collections}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching collections: {str(e)}"
        )


@app.get("/database/collections/{collection_name}/documents")
async def get_documents(collection_name: str, limit: int = 100, skip: int = 0):
    """Returns documents from a specific collection with pagination."""
    try:
        if collection_name not in db.list_collection_names():
            raise HTTPException(
                status_code=404, detail=f"Collection '{collection_name}' not found"
            )

        # Get the collection
        target_collection = db[collection_name]

        # Count total documents
        total_documents = target_collection.count_documents({})

        # Get documents with pagination
        documents = list(
            target_collection.find({}, {"_id": False})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        return {
            "collection": collection_name,
            "total_documents": total_documents,
            "documents": documents,
            "page": {
                "limit": limit,
                "skip": skip,
                "has_more": (skip + limit) < total_documents,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching documents: {str(e)}"
        )


@app.get("/database/stats")
async def get_database_stats():
    """Returns statistics about the database and its collections."""
    try:
        stats = {"database": db.name, "collections": [], "total_documents": 0}

        for collection_name in db.list_collection_names():
            collection_stats = {
                "name": collection_name,
                "document_count": db[collection_name].count_documents({}),
            }
            stats["collections"].append(collection_stats)
            stats["total_documents"] += collection_stats["document_count"]

        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching database stats: {str(e)}"
        )


@app.get("/database/list")
async def list_databases():
    """Returns a list of all databases in the MongoDB cluster."""
    try:
        # Get list of all databases
        databases = client_db.list_database_names()

        # Filter out system databases if desired
        filtered_databases = [
            db_name
            for db_name in databases
            if db_name not in ["admin", "local", "config"]
        ]

        # Get basic stats for each database
        db_stats = []
        for db_name in filtered_databases:
            current_db = client_db[db_name]
            collections = current_db.list_collection_names()

            db_info = {
                "name": db_name,
                "collections": len(collections),
                "collection_names": collections,
            }
            db_stats.append(db_info)

        return {"total_databases": len(filtered_databases), "databases": db_stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error listing databases: {str(e)}"
        )


@app.post("/configure")
async def configure_assistant(
    file: UploadFile = File(...), prompt_text: str = Form(...)
):
    """
    Configure a new assistant with the uploaded file and prompt text.

    Args:
        file: The file to upload and use with the assistant
        prompt_text: The text to use as instructions for the assistant

    Returns:
        dict: Information about the created assistant
    """
    try:
        # Create a temporary file to store the uploaded content
        temp_file_path = os.path.join(TMP_DIR, file.filename)

        # Save the uploaded file to the temporary location
        with open(temp_file_path, "wb") as temp_file:
            # Read the uploaded file in chunks to handle large files
            shutil.copyfileobj(file.file, temp_file)

        # Create the assistant with the vector store
        assistant_response = create_assistant_with_vector_store(
            temp_file_path, prompt_text
        )

        # Extract the assistant ID from the response
        assistant_id = assistant_response.get("id")

        # Update the ASSISTANT_ID global variable for future requests
        global ASSISTANT_ID
        ASSISTANT_ID = assistant_id
        print(f'Assistant ID: {ASSISTANT_ID}')
        
        # Clean up - delete the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # Return the assistant information
        return {
            "message": "Assistant configured successfully",
            "assistant_id": assistant_id,
            "assistant_details": assistant_response,
        }

    except Exception as e:
        # Clean up in case of error
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # Raise an HTTP exception with the error details
        raise HTTPException(
            status_code=500, detail=f"Error configuring assistant: {str(e)}"
        )
