
import google.generativeai as genai
import os

from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("LLM_API_KEY"))

chat_model = genai.GenerativeModel("models/gemini-2.5-flash")

chat_session = chat_model.start_chat()


def chatbot_answer(query, context_chunks):
    """
    Answer user query using Gemini with provided context chunks from PDF.
    """
    context = "\n\n".join(context_chunks)
    response = chat_session.send_message(
        f"Answer the following question using only the context:\n\n{context}\n\nQuestion: {query}"
    )
    return response.text
