import os
import asyncio
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from handlers.chat import reset_conversation, handle_stream
from service.search import create_search_engine
from utils.generator import to_sync_generator
from graphrag.query.context_builder.conversation_history import ConversationHistory


st.markdown(
    r"""
    <style>
    .stAppDeployButton {
        visibility: hidden;
    }
    .stMainMenu {
        visibility: hidden;
    }
    </style>
    """, unsafe_allow_html=True
)

def start():
    search_engine = create_search_engine()
    load_dotenv()

    st.title("Chat with your PDFs")


    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask a question"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = search_engine.astream_search(
                prompt,
                conversation_history=ConversationHistory.from_list(
                    [
                        {"role": x["role"], "content": x["content"]}
                        for x in st.session_state.messages
                    ]
                ),
            )
            response = st.write_stream(to_sync_generator(stream, handler=handle_stream))

        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    start()
