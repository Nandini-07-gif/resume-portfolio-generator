import os
import re

def clean_resume_text(raw_text: str) -> str:
    """Cleans raw text by removing extra spaces and weird characters."""
    cleaned_text = re.sub(r'[\r\t]', ' ', raw_text)
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
    return cleaned_text.strip()

def get_resume_input() -> str:
    """Asks the user how they want to provide their resume content."""
    print("How would you like to enter your resume?")
    print("1. Read from 'resume.txt'")
    print("2. Paste/Type raw text directly")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        file_path = "resume.txt"
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found!")
            return ""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
            
    elif choice == "2":
        print("\nPaste your resume text below (Press Enter, then Ctrl+D or Ctrl+Z and hit Enter to finish):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        return "\n".join(lines)
    else:
        print("Invalid choice.")
        return ""

if __name__ == "__main__":
    raw_content = get_resume_input()
    
    if raw_content:
        cleaned_resume = clean_resume_text(raw_content)
        print("\n--- Cleaned Resume Output ---")
        print(cleaned_resume)