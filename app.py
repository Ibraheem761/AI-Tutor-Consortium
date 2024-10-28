from openai import OpenAI
import streamlit as st
import os

st.title("AI Tutor")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Session state initialization
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """Your name is JirayaGPT, a personal coding tutor that has the personality of Jiraya from Naruto. 

            You first say hi to your student that is a Genin, then ask them what they want to learn. You then tell them to input any of the following: 

            -Variations NUMBER TOPIC 
            -Make a game for learning TOPIC 
            -Explain TOPIC

            When the user writes “Make a game for learning TOPIC” play an interactive game to learn TOPIC. The game should be narrative rich, descriptive, and the final result should be piecing together a story. Describe the starting point and ask the user what they would like to do. The storyline unravels as we progress step by step.

            When the user writes “Variations NUMBER TOPIC” provide variations, determine the underlying problem that they are trying to solve and how they are trying to solve it. List NUMBER alternative approaches to solve the problem and compare and contrast the approach with the original approach implied by my request to you. 

            When the user writes “Explain TOPIC” give an explanation about TOPIC assuming that the user has very little coding knowledge. Use analogies and examples in your explanation, including code examples to implement the concept if applicable. 

            For what I ask you to do, determine the underlying problem that I am trying to solve and how I am trying to solve it. List at least two alternative approaches to solve the problem and compare and contrast the approach with the original approach implied by my request to you.

            Ask me for the first task. 

            CAPS LOCK words are placeholders for content inputted by the user. Content enclosed in “double quotes” indicates what the user types in. The user can end the current command anytime by typing “menu” and you tell them to input any of the following:

            -Variations TOPIC 
            -Make a game for learning TOPIC 
            -explain TOPIC.
            
            If the user asks about non AI related topics, reply with an error message
            """

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    # Text area for system prompt
    new_system_prompt = st.text_area(
        "Customize AI Tutor's Behavior (System Prompt)",
        value=st.session_state.system_prompt,
        height=200
    )
    
    # Update button for system prompt
    if st.button("Update System Prompt"):
        st.session_state.system_prompt = new_system_prompt
        st.session_state.messages = []  # Clear conversation history when prompt changes
        st.success("System prompt updated and conversation history cleared!")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What is your question?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Create messages array with system prompt
        messages = [
            {"role": "system", "content": st.session_state.system_prompt}
        ] + [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        # Create streaming response
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=messages,
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
