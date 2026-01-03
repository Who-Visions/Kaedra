
import os
from rich.console import Console
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Config
load_dotenv()
console = Console()

def test_url_context():
    # Use standard API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        console.print("[red]API Key not found![/]")
        return

    client = genai.Client(api_key=api_key)
    
    # Test Prompt: Compare Python 3.12 vs 3.11 features from docs
    url1 = "https://docs.python.org/3/whatsnew/3.12.html"
    url2 = "https://docs.python.org/3/whatsnew/3.11.html"
    
    prompt = f"Briefly summary 3 key differences between Python 3.12 and 3.11 based ONLY on these URLs: {url1} and {url2}"
    
    console.print(f"[bold cyan]Asking Gemini 3 Flash Preview to compare URLs...[/]")

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(url_context=types.UrlContext())]
            ),
        )

        console.print("\n[bold green]Response:[/]")
        console.print(response.text)

        # Correct attribute access based on SDK version (v1beta vs v1alpha vs latest)
        # Checking candidate attributes dynamically if needed, but standard is `url_context_metadata`
        candidate = response.candidates[0]
        
        # Try to access metadata safely
        metadata = getattr(candidate, 'url_context_metadata', None)
        
        if metadata:
            console.print("\n[bold yellow]URL Context Metadata:[/]")
            for url_data in metadata.url_metadata:
                 console.print(f"- {url_data.retrieved_url}: [blue]{url_data.url_retrieval_status}[/]")

    except Exception as e:
        console.print(f"[red]Error:[/]\n{e}")

if __name__ == "__main__":
    test_url_context()
