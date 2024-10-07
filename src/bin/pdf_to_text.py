import sys
from PyPDF2 import PdfReader


"""
Usage: `python ./src/bin/pdf_to_text.py PATH_TO_PDF
"""
if __name__ == "__main__":
    reader = PdfReader(sys.argv[1])
    number_of_pages = len(reader.pages)
    pages = reader.pages
    text = "\n\n".join([p.extract_text() for p in pages])
    name = sys.argv[1].split("/")[-1].split(".")[0]
    with open(f"./knowledge_base/{name}.txt", "w") as text_file:
        text_file.write(text)
