# Chat with PDFs

A minimalistic chatbot tailored for answering questions on provided documents. Built using Streamlit and GraphRag. Emphasis is on quality and accuracy of responses.

## Requirements

- `python 3.11`
- An OpenAI API key

## Setup

_All commands must be run from the root directory._

1.  Create a .env file from the .env.sample file and enter your OpenAI API key for both environment variables.
2.  Install python dependencies - `pip install -r requirements.txt`
3.  Create a .txt version of the PDF(s) that we want to feed the chatbot e.g
    `python ./src/bin/pdf_to_text.py assets/PepsiCo-Global-Human-Rights-Policy.pdf`
4.  Setup the chatbot's knowledge base - `python -m graphrag.index --root ./`
5.  Run the chatbot - `streamlit run src/app.py`
