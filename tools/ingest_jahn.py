
import os
from google import genai
from google.genai import types
from pathlib import Path

def ingest_jahn():
    # Use standard API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    
    if not api_key and os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
                elif line.startswith("GOOGLE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()

    client = genai.Client(api_key=api_key, vertexai=False)
    
    pdf_path = r"c:\Users\super\Downloads\pppf.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    print(f"Ingesting Manfred Jahn's Narratology PDF: {pdf_path}")
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    prompt = """
    Analyze Manfred Jahn's 'A Guide to Narratological Film Analysis'.
    Extract exactly 7 sophisticated 'Narratological Audit' filters for an AI Review Board.
    Focus on:
    1. FCD (Filmic Composition Device) Intentionality: Is the creative intelligence clear?
    2. Focalization Nuance: Distinguish between DIV, PIV, and OV effectively.
    3. The Audio Code: How sound/silence is used narratologically.
    4. OPI (Online Perception Illusion): Strategies of deception.
    5. Transcripts & Storyboards: Relationship between text and visual panels.
    6. Reality Effect vs. Goofs: Audit for verisimilitude.
    7. Communicative Cooperation: Is the FCD being cooperative or using 'mind-bender' tactics?

    Format as a structured System Instruction block for an AI Council.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt
            ]
        )
        
        output_path = Path("kaedra/config/jahn_narratology_directives.txt")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(response.text, encoding="utf-8")
        print(f"Directives saved to {output_path}")
        print("\nNARRATOLOGICAL DIRECTIVES:")
        print(response.text)
        
    except Exception as e:
        print(f"Error ingesting PDF: {e}")

if __name__ == "__main__":
    ingest_jahn()
