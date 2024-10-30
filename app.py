from openai import OpenAI
import streamlit as st
import os
from PIL import Image
import base64
import io
from PyPDF2 import PdfReader
from docx import Document
from typing import List, Dict, Union

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_system_prompt(file_path="system_prompt.txt"):
    """Load system prompt from file, create default if doesn't exist"""
    default_prompt = """Your name is JirayaGPT, a personal coding tutor that has the personality of Jiraya from Naruto. 
    If the user asks about non AI related topics, reply with an error message"""
    
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        # Create file with default prompt if it doesn't exist
        with open(file_path, 'w') as file:
            file.write(default_prompt)
        return default_prompt

def extract_text_from_pdf(file_bytes) -> str:
    """Extract text from PDF using PyPDF2"""
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    text_content = []
    
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content.append(f"Page {page_num + 1}:\n{page.extract_text()}")
    
    return "\n".join(text_content)

def extract_text_from_docx(file_bytes) -> str:
    """Extract text from DOCX file"""
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def process_uploaded_file(uploaded_file) -> Union[Dict, None]:
    """Process the uploaded file and return appropriate content"""
    if uploaded_file is None:
        return None
    
    file_type = uploaded_file.type
    
    if file_type.startswith('image'):
        image = Image.open(uploaded_file)
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        image_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{image_str}",
                "detail": "high"
            }
        }
    
    elif file_type == 'application/pdf':
        text_content = extract_text_from_pdf(uploaded_file.getvalue())
        return {"type": "text", "text": text_content}
    
    elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        text_content = extract_text_from_docx(uploaded_file.getvalue())
        return {"type": "text", "text": text_content}
    
    elif file_type == 'text/plain':
        return {"type": "text", "text": uploaded_file.getvalue().decode()}
    
    return None

# Page config and header
st.set_page_config(page_title="AI Tutor")
st.image('Logo_Landscape_Colored.png', width=300)
st.title("AI Tutor")

# Initialize session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4-vision-preview"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = load_system_prompt()
if "document_content" not in st.session_state:
    st.session_state.document_content = None

# Sidebar for settings and file upload
with st.sidebar:
    st.header("Settings")
    
    # System prompt editor
    new_system_prompt = st.text_area(
        "Customize AI Tutor's Behavior (System Prompt)",
        value=st.session_state.system_prompt,
        height=200
    )
    
    # Save system prompt to file
    if st.button("Update System Prompt"):
        with open("system_prompt.txt", "w") as f:
            f.write(new_system_prompt)
        st.session_state.system_prompt = new_system_prompt
        st.session_state.messages = []
        st.success("System prompt updated and saved to file!")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload a file for discussion",
        type=['png', 'jpg', 'jpeg', 'pdf', 'docx', 'txt']
    )
    
    # Clear chat button
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.document_content = None
        st.experimental_rerun()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], str):
            st.markdown(message["content"])
        elif isinstance(message["content"], list):
            for content in message["content"]:
                if isinstance(content, dict):
                    if content.get("type") == "image_url":
                        image_url = content["image_url"]["url"]
                        if image_url.startswith('data:image'):
                            image_data = base64.b64decode(image_url.split(',')[1])
                            st.image(image_data)
                    elif content.get("type") == "text":
                        st.markdown(content["text"])
                else:
                    st.markdown(str(content))

# Chat input
if prompt := st.chat_input("What is your question?"):
    # Process any uploaded file
    file_content = process_uploaded_file(uploaded_file)
    
    # Prepare message content
    if file_content:
        message_content = [{"type": "text", "text": prompt}, file_content]
    else:
        message_content = prompt
    
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": message_content})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        if file_content:
            if file_content.get("type") == "image_url":
                image_url = file_content["image_url"]["url"]
                if image_url.startswith('data:image'):
                    image_data = base64.b64decode(image_url.split(',')[1])
                    st.image(image_data)
            elif file_content.get("type") == "text":
                with st.expander("Uploaded Document Content"):
                    st.markdown(file_content["text"])
    
    # Generate assistant response
    with st.chat_message("assistant"):
        messages = [
            {"role": "system", "content": st.session_state.system_prompt}
        ] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=messages,
            stream=True,
        )
        response = st.write_stream(stream)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
