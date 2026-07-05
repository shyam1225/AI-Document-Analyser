from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from docx import Document
import PyPDF2
import base64
from dotenv import load_dotenv
import os 
from sentence_transformers import SentenceTransformer
import faiss 
import numpy as np
load_dotenv()
text=""
chunks=[]
index=None
global chat_history
global history_text
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",  
   )
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def create_chunks(text, chunk_size=1000):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

def create_vector_store(chunks):
    embeddings=embedding_model.encode(chunks, convert_to_numpy=True)
    embeddings=embeddings.astype("float32")
    faiss.normalize_L2(embeddings)
    dimension=embeddings.shape[1]  
    index=faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index

def find_relevant_chunks(chunks, question, index, k=3):
    question_embedding=embedding_model.encode([question],convert_to_numpy=True)
    question_embedding=question_embedding.astype("float32")
    faiss.normalize_L2(question_embedding)
    scores,indices=index.search(question_embedding,k)
    relevant=[]
    for i in indices[0]:
        relevant.append(chunks[i])
    return relevant

def extract_image_text(file):
    image_bytes = file.read()

    base64_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
Extract all useful information from this image.

Include:
- visible text
- diagrams
- labels
- charts
- tables
- important details
answer in pointwise format. Start each point with a new line and a hyphen.

Return only the extracted information.
"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":
                            f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

app = Flask(__name__)
text = ""
chunks = []

@app.route("/")
def home():
    return render_template("asa.html")

@app.route("/upload", methods=["POST"])
def upload():

    global text
    global index
    global chunks
    
    try:
            
        text=""
        global chat_history
        chat_history=[]
        print("UPLOAD CALLED")
        files = request.files.getlist("files")
        for file in files:
            print("Processing:", file.filename)
        print("Files received:", len(files))
        for file in files:
            filename = file.filename.lower()
            if filename.endswith(".pdf"):

                reader = PyPDF2.PdfReader(file)

                for page in reader.pages:

                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"

            elif filename.endswith(".txt"):
                text += (file.read().decode("utf-8") + "\n")
            elif filename.endswith(".docx"):
                document = Document(file)
                for para in document.paragraphs:
                    text += para.text + "\n"

            elif filename.endswith((".png", ".jpg", ".jpeg", ".webp")):
                image_text = extract_image_text(file)
                text += image_text + "\n"
            else:

                return jsonify(
                    {
                        "answer":
                        f"Unsupported file type: {file.filename}"
                    }
                )
        chunks = create_chunks(text)
        index = create_vector_store(chunks)
        print("Files received:", len(files))
        print("Text length:", len(text))
        print("Chunks created:", len(chunks))
        print("Index created:", index.ntotal)

    except Exception as e:
        print("UPLOAD ERROR:", str(e))

    if not text.strip():

        return jsonify(
            {
                "answer":
                "No readable content found in uploaded files."
            }
        )

    return jsonify({
    "answer": "Files uploaded successfully"
    })

@app.route("/ask", methods=["POST"])
def ask():
    print("ASK CALLED")
    global index
    global chunks
    global chat_history
    history_text=""
    for item in chat_history[-5:]:
            history_text += f"""
            User: {item['question']}
            Assistant: {item['answer']}
            """
    print("index =", index)
    print("chunks =", len(chunks))
    print("chat history=", history_text)
    if index is None:
        return jsonify({
            "answer": "Please upload a document first."
        })
    print("Request received")
    question = request.form["question"]
    print(f"Question: {question}")
    relevant_chunks = find_relevant_chunks(chunks, question,index)
    context = "\n\n".join(relevant_chunks)
    
    
    prompt = f"""
You are a document question-answering assistant.
Below is how you should answer different types of questions-
1. If the question is asking for a summary of the document, provide a concise summary based on the context.
2. If the question is asking for steps ,procedures, or instructions, provide a clear step-by-step answer based on the context.
3. If the question is asking for a list of items, provide a bullet-point list based on the context.
4. If the question is asking for an explanation of a concept, provide a detailed explanation based on the context.
5. If the question is asking for a comparison, return ONLY an HTML table followed by a brief summary. Use <table>, <tr>, <th>, and <td> tags.
6. If the question is asking for specific information, provide a direct answer based on the context.
7. If the question is asking for a graph/chart, return ONLY valid JSON.
Example of valid JSON format for a chart answer, pleaae stick to this format DO NOT return anything else apart from this.
{{
  "type":"chart",
  "chart_type":"line",
  "title":"Sales Growth",
  "labels": ["2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019"],
  "values": [19, 47, 91, 130, 185, 230, 278, 320]
}}
8. For any other types of questions, provide the most relevant answer based on the context.
9. Mention the source of the information in the answer.
10.Answer based on the document context and previous conversation.
11.While responding consider previous conversation history according to the question.

Previous conversation:
{history_text}
 
CONTEXT:
{context}

QUESTION:
{question}
"""

    try:

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )
        answer = response.choices[0].message.content
        
        chat_history.append({
            "question": question,
            "answer": answer
            })
        
        return jsonify(
            {
                "answer": answer
            }
        )
    
    except Exception as e:
        print("LLM Error:", e)
        return jsonify(
            {
                "answer":
                f"Error generating answer: {str(e)}"
            }
        )
    
    
if __name__ == "__main__":
    app.run(debug=True)
text = ""
chunks = []
index = None


