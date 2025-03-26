# 🚀 Project Name

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
The **Email Request Classification and Processing System** is an innovative solution designed to automate the handling of loan servicing request emails. It processes emails with attachments (DOC, PDF, text, or images), classifies request types, extracts detailed sub-requests, and identifies similar past emails using advanced AI and vector search technology. This project tackles the problem of manually processing large volumes of customer service emails in industries like banking and finance, aiming to boost efficiency, reduce errors, and enhance response times for customer inquiries.



## 🎥 Demo
🔗 [Live Demo](https://email-processor.netlify.app/)  
📹 [Video Demo](#) (if applicable)  
🖼️ Screenshots:
![image](https://github.com/user-attachments/assets/da55c1dd-ac10-454d-bb7f-20aefe4433fd)
![image](https://github.com/user-attachments/assets/91c43bf2-c315-4e38-897f-02ab12121714)
![image](https://github.com/user-attachments/assets/9a7bb5da-6c30-4f41-bae0-f60228312416)


## 💡 Inspiration
The inspiration for this project stemmed from the overwhelming workload faced by customer service teams in the financial sector. Loan servicing departments often receive hundreds of emails daily, each requiring manual classification and response—a process that’s slow, repetitive, and prone to mistakes. We envisioned a system that leverages AI to automate email classification, extract critical details, and detect duplicates, freeing up human agents to focus on complex tasks and improving overall service quality.


## ⚙️ What It Does
This system offers a robust set of features to streamline email processing:
Email Classification: Automatically identifies the request type (e.g., "Loan Balance Inquiry") using AI-powered analysis.

* **Sub-Request Extraction**: Pulls out specific details (e.g., "Loan Account Number," "Interest Rate") with confidence scores for reliability.

* **Duplicate Detection**: Uses vector search to compare new emails against past ones, flagging potential duplicates to avoid redundant work.

* **Attachment Processing**: Extracts text from various attachment types (DOC, PDF, text, images) to ensure all relevant information is analyzed.

* **Scalable Storage**: Stores emails and their embeddings in MongoDB for fast retrieval and similarity searches.

For example, an email like "Please provide my current loan balance for account 123456789" with a PDF attachment would be classified, have its details extracted, and checked against past emails—all in seconds!



## 🛠️ How We Built It
We crafted this system with a modern, scalable tech stack:
* **FastAPI**: Built a RESTful API in Python using FastAPI to handle email submissions and attachment uploads via a /process_email endpoint.

* **OpenAI API**: Leveraged GPT-4 for classifying request types and extracting sub-requests, and the embedding API (e.g., text-embedding-ada-002) for generating vectors for similarity checks.

* **MongoDB Atlas**: Implemented a database with vector search capabilities to store emails and perform nearest-neighbor searches for duplicate detection.

* **Text Extraction**: Used libraries like PyPDF2 (for PDFs), python-docx (for DOCX), and pytesseract (for OCR on images) to process attachments.

* **Kubernetes**: Deployed the application on Kubernetes to ensure scalability and reliability under high email volumes.

* **Dataset Utilization**: Employed a JSON dataset of 180 labeled emails for few-shot learning and pre-computing embeddings, enhancing classification accuracy.

The workflow starts with text extraction, followed by embedding generation and vector search for classification, then LLM-based extraction, and finally storage and response generation.



## 🚧 Challenges We Faced
Building this system wasn’t without hurdles:
* **Diverse Attachments**: Extracting text from varied file formats—especially scanned PDFs and images—required integrating OCR and ensuring compatibility across types.

* **Duplicate Detection Accuracy**: Fine-tuning vector search similarity thresholds in MongoDB to catch true duplicates without excessive false positives was tricky.

* **Cost and Rate Limits**: Managing OpenAI API usage for classification, extraction, and embeddings while staying within budget and avoiding rate limits posed a balancing act.

* **Scalability**: Ensuring the system could handle large email volumes led us to Kubernetes, but configuring it for optimal performance took extra effort.



## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone https://github.com/gaied-doubledragon.git
   ```
2. Install dependencies
   Ensure Python 3.8+ is installed, then run:   
   ```sh
   cd code/backend/fastapi
   pip install -r requirements.txt (for Python)
   ```

3. Run the backend
   Create a .env file and add OPEN_AI_KEY and MONGO_URI
   then run,
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
5. Open a new terminal
   then run:   
   ```sh
   cd code/frontend/
   npm install
   ```
6. Run the frontend
   ```sh
   npm run dev
   ```

## 🏗️ Tech Stack
- 🔹 Frontend: React
- 🔹 AI/ML: OpenAI API (GPT-4 for classification/extraction, embeddings for vector search)
- 🔹 Text Extraction (OCR): PyPDF2 (PDFs), python-docx (DOCX), pytesseract (OCR for images) 
- 🔹 Deployment: Docker, Kuberenetes – Ensures scalability and resilience 
- 🔹 Backend: FastAPI (Python) – Lightweight, fast API framework
- 🔹 Database: MongoDB Atlas – Scalable storage with vector search  
- 🔹 Other: Uvicorn (ASGI server), Pymongo (MongoDB driver)


## 👥 Team
- **Yajat Malhotra** - [GitHub](https://github.com/iamyajat) | [LinkedIn](https://www.linkedin.com/in/iamyajat/)
- **Himanshu Thakur** - [GitHub](https://github.com/himanshu-thakur-7) | [LinkedIn](https://www.linkedin.com/in/himanshu-thakur-9582631a6/)
