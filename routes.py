from flask import render_template, request, jsonify

from document_processor import (
    create_chunks,
    extract_text_from_file
)

from vector_store import (
    create_vector_store,
    find_relevant_chunks
)

from llm_service import ask_llm

from prompts import document_qa_prompt


def register_routes(app, state):

    @app.route("/")
    def home():

        return render_template("asa.html")


    @app.route("/upload", methods=["POST"])
    def upload():

        files = request.files.getlist("files")

        if not files:
            return jsonify({
                "answer": "No files uploaded."
            })

        try:

            new_text = ""

            # Extract text from newly uploaded files
            for file in files:

                if not file.filename:
                    continue

                print("Processing:", file.filename)

                new_text += extract_text_from_file(file)

            if not new_text.strip():

                return jsonify({
                    "answer": "No readable content found in uploaded files."
                })

            # Create chunks for the new documents
            new_chunks = create_chunks(new_text)

            # Add new chunks to existing chunks
            state["chunks"].extend(new_chunks)

            # Rebuild FAISS index using ALL documents
            state["index"] = create_vector_store(
                state["chunks"]
            )

            # Keep complete extracted text as well
            state["text"] += new_text

            print(
                "New chunks:",
                len(new_chunks)
            )

            print(
                "Total chunks:",
                len(state["chunks"])
            )

            print(
                "Total index vectors:",
                state["index"].ntotal
            )

            return jsonify({
                "answer": "Files uploaded successfully"
            })

        except Exception as e:

            print(
                "UPLOAD ERROR:",
                e
            )

            return jsonify({
                "answer":
                f"Error processing files: {str(e)}"
            })

    @app.route("/ask", methods=["POST"])
    def ask():

        index = state["index"]
        chunks = state["chunks"]
        chat_history = state["chat_history"]

        print("ASK CALLED")
        print("index =", index)
        print("chunks =", len(chunks))

        if index is None:

            return jsonify({
                "answer":
                "Please upload a document first."
            })

        question = request.form.get(
            "question",
            ""
        ).strip()

        if not question:

            return jsonify({
                "answer":
                "Please enter a question."
            })

        print(
            "Question:",
            question
        )

        # Search existing FAISS index
        relevant_chunks = find_relevant_chunks(
            chunks,
            question,
            index
        )

        context = "\n\n".join(
            relevant_chunks
        )

        # Build conversation history
        history_text = ""

        for item in chat_history[-5:]:

            history_text += f"""
User: {item['question']}
Assistant: {item['answer']}
"""

        # Create prompt
        prompt = document_qa_prompt(
            history_text,
            context,
            question
        )

        try:

            answer = ask_llm(prompt)

            # Save conversation
            chat_history.append({
                "question": question,
                "answer": answer
            })

            return jsonify({
                "answer": answer
            })

        except Exception as e:

            print(
                "LLM Error:",
                e
            )

            return jsonify({
                "answer":
                f"Error generating answer: {str(e)}"
            })