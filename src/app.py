
import streamlit as st
import pandas as pd
import tempfile
import os
import json
import sys


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from extractor import extract_esg
from pdf_reader import read_pdf_text_by_page
from gemini_extractor import extract_with_gemini
from chatbot import chatbot_answer


if "gemini_metrics" not in st.session_state:
    st.session_state.gemini_metrics = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


st.set_page_config(page_title="ESG Report Analyzer", layout="wide")
st.title("📊 ESG Report Analyzer")


uploaded_file = st.file_uploader("Upload an ESG PDF", type=["pdf"])

if uploaded_file is not None:
   
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_pdf_path = tmp_file.name

  
    df = extract_esg(temp_pdf_path)

    if not df.empty:
   
        df_display = df.rename(columns={
            "company_name": "Company Name",
            "metric": "Metric Name",
            "unit": "Unit",
            "value": "Value",
            "year": "Year",
            "source_page": "Source Page"
        })

      
        columns_order = ["Company Name", "Metric Name", "Unit", "Value", "Year", "Source Page"]
        for col in columns_order:
            if col not in df_display.columns:
                df_display[col] = ""
        df_display = df_display[columns_order]

        st.subheader(f"🔍 Extracted ESG Metrics (Regex-based) for: {uploaded_file.name}")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.warning("No ESG metrics were found in the uploaded file.")




    st.subheader("💬 Chat with the ESG Report")

    user_query = st.text_input("Ask a question about the report:")

    if st.button("Send") and user_query:
        with st.spinner("🤖 Thinking..."):
      
            st.session_state.chat_history.append(("You", user_query))

         
            context_chunks = []
            if st.session_state.gemini_metrics:
                context_chunks = [
                    f"{m}: {d.get('value')}" if isinstance(d, dict) else f"{m}: {d}"
                    for m, d in st.session_state.gemini_metrics.items()
                ]

          
            pages = read_pdf_text_by_page(temp_pdf_path)
            context_chunks.extend(pages[:20]) 

         
            answer = chatbot_answer(user_query, context_chunks)

           
            st.session_state.chat_history.append(("Bot", answer))

   
    if st.session_state.chat_history:
        for role, msg in st.session_state.chat_history:
            if role == "You":
                st.markdown(f"**🧑 {role}:** {msg}")
            else:
                st.markdown(f"**🤖 {role}:** {msg}")
