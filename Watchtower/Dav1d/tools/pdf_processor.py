"""
PDF Processor for Dav1d
Extracts text from PDFs and digests them using Gemini.
"""

import os
import argparse
import sys
from pypdf import PdfReader
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID", "gen-lang-client-0285887798")
LOCATION = os.getenv("LOCATION", "us-east4")

# Initialize Gemini
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"Warning: Gemini not available ({e}). Will only extract text.", file=sys.stderr)
    GEMINI_AVAILABLE = False

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text content from a PDF file."""
    print(f"📖 Reading: {pdf_path}...")
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n{page_text}"
        return text
    except Exception as e:
        print(f"❌ Error reading PDF: {e}", file=sys.stderr)
        return ""

def digest_text(text: str, title: str) -> str:
    """Uses Gemini to summarize/digest the text."""
    if not GEMINI_AVAILABLE:
        return "Gemini unavailable for digestion."
    
    print(f"🧠 Digesting '{title}' with Gemini...")
    
    prompt = f"""You are an expert researcher. Digest this PDF content.

Title: {title}

Content (truncated if too long):
{text[:30000]} 

... [Content Truncated] ...

Task:
1. Provide a high-level summary (Executive Summary).
2. List the Key Takeaways (Bullet points).
3. Identify any Actionable Advice.
4. Provide a "Dav1d's Take" - a cynical/realist perspective on this content.

Format as Markdown.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3
            )
        )
        return response.text
    except Exception as e:
        return f"❌ Digest failed: {e}"

def main():
    parser = argparse.ArgumentParser(description="Dav1d PDF Processor")
    parser.add_argument("path", help="Path to PDF file or directory")
    parser.add_argument("--output", "-o", help="Output directory for digests", default="resources/digests")
    args = parser.parse_args()

    target_path = args.path
    output_dir = args.output
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files_to_process = []
    if os.path.isfile(target_path) and target_path.lower().endswith(".pdf"):
        files_to_process.append(target_path)
    elif os.path.isdir(target_path):
        for root, dirs, files in os.walk(target_path):
            for file in files:
                if file.lower().endswith(".pdf"):
                    files_to_process.append(os.path.join(root, file))
    
    if not files_to_process:
        print("No PDF files found.")
        return

    print(f"Found {len(files_to_process)} PDFs to process.")

    for pdf_file in files_to_process:
        base_name = os.path.basename(pdf_file)
        name_no_ext = os.path.splitext(base_name)[0]
        
        # 1. Extract
        raw_text = extract_text_from_pdf(pdf_file)
        if not raw_text:
            continue
            
        # Save raw text
        txt_path = os.path.join(output_dir, f"{name_no_ext}_raw.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"💾 Saved raw text: {txt_path}")

        # 2. Digest
        digest = digest_text(raw_text, name_no_ext)
        
        # Save digest
        digest_path = os.path.join(output_dir, f"{name_no_ext}_digest.md")
        with open(digest_path, "w", encoding="utf-8") as f:
            f.write(f"# Digest: {name_no_ext}\n\n{digest}")
        print(f"✅ Saved digest: {digest_path}\n")

if __name__ == "__main__":
    main()
