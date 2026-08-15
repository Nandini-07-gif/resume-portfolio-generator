import os
import re

def load_and_clean_resume(file_path: str) -> str:
    """Reads a text resume file and returns cleaned text."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        raw_text = file.read()

    # Clean tabs, carriage returns, extra spaces, and extra lines
    cleaned_text = re.sub(r'[\r\t]', ' ', raw_text)
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)

    return cleaned_text.strip()


if __name__ == "__main__":
    try:
        cleaned_resume = load_and_clean_resume("resume.txt")
        print("--- Cleaned Resume Output ---")
        print(cleaned_resume)
    except Exception as e:
        print(f"Error: {e}")