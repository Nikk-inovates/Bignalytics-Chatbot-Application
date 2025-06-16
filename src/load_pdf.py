import os
import fitz  # PyMuPDF
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="📄 [%(levelname)s] %(asctime)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def load_pdf_text(file_path: str) -> str:
    """
    Extracts and returns text content from a given PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: The extracted full text from the PDF.

    Raises:
        ValueError: If input is invalid or content is empty.
        FileNotFoundError: If the file does not exist.
        Exception: For any reading/parsing failure.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("❌ No file path provided or invalid format.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError("❌ The provided file must be a PDF (.pdf extension).")

    try:
        logging.info(f"📥 Loading PDF: {file_path}")
        doc = fitz.open(file_path)

        if doc.page_count == 0:
            raise ValueError("❌ The PDF has no pages.")

        text_pages = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text().strip()

            if not page_text:
                logging.warning(f"⚠️ Page {page_num + 1} contains no readable text.")
            else:
                text_pages.append(page_text)

        full_text = "\n".join(text_pages).strip()

        if not full_text:
            raise ValueError("❌ No readable text found in the PDF.")

        logging.info("✅ PDF text extraction successful.")
        return full_text

    except Exception as e:
        raise Exception(f"❌ Failed to read PDF: {e}")
import os
import fitz  # PyMuPDF
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="📄 [%(levelname)s] %(asctime)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def load_pdf_text(file_path: str) -> str:
    """
    Extracts and returns text content from a given PDF file.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        str: The extracted full text from the PDF.

    Raises:
        ValueError: If input is invalid or content is empty.
        FileNotFoundError: If the file does not exist.
        Exception: For any reading/parsing failure.
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("❌ No file path provided or invalid format.")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ File not found: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError("❌ The provided file must be a PDF (.pdf extension).")

    try:
        logging.info(f"📥 Loading PDF: {file_path}")
        doc = fitz.open(file_path)

        if doc.page_count == 0:
            raise ValueError("❌ The PDF has no pages.")

        text_pages = []
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            page_text = page.get_text().strip()

            if not page_text:
                logging.warning(f"⚠️ Page {page_num + 1} contains no readable text.")
            else:
                text_pages.append(page_text)

        full_text = "\n".join(text_pages).strip()

        if not full_text:
            raise ValueError("❌ No readable text found in the PDF.")

        logging.info("✅ PDF text extraction successful.")
        return full_text

    except Exception as e:
        raise Exception(f"❌ Failed to read PDF: {e}")
