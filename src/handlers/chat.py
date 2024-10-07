import streamlit as st
import re
import pandas as pd
from typing import AsyncGenerator


async def handle_stream(stream: AsyncGenerator):
    context_records = {}
    in_citation = False
    has_citation = False

    async for chunk in stream:
        if isinstance(chunk, dict):
            context_records = chunk
            continue
        if isinstance(chunk, str):
            has_open = chunk.find("[")
            has_close = chunk.find("]")

            # case where we have a full citation in the chunk
            if has_open != -1 and has_close != -1 and not in_citation:
                has_citation = True
                chunk = chunk[:has_open] + chunk[has_close + 1 :]

            # case where we saw an open '[' in the chunk
            elif has_open != -1 and not in_citation:
                has_citation = True
                chunk = chunk[:has_open]
                in_citation = True

            # case where we've seen an open '[' and now we see a close ']'
            elif has_close != -1 and in_citation:
                chunk = chunk[has_close + 1 :]
                in_citation = False

            # case we are in a citation and we can't see a closing ']'
            elif in_citation:
                continue
        yield chunk
    if has_citation:
        df = context_records["sources"].rename(
            columns={"id": "source", "text": "content"}
        )[["source", "content"]]
        df["content"] = "..." + df["content"].astype(str) + "..."
        st.write("<h3>Sources</h3>", unsafe_allow_html=True)
        yield df


def reset_conversation():
    st.session_state.conversation = None
    st.session_state.chat_history = None
