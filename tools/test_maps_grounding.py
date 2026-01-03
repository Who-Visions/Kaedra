
import os
from rich.console import Console
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Config
load_dotenv()
console = Console()

def test_maps_grounding():
    # Use standard API key from environment
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        console.print("[red]API Key not found![/]")
        return

    client = genai.Client(api_key=api_key)
    
    # Test Prompt
    prompt = "What are the best coffee shops within a 10-minute walk from the Empire State Building?"
    
    console.print(f"[bold cyan]Asking Gemini 3 Flash Preview:[/]\n'{prompt}'\n")

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_maps=types.GoogleMaps(enable_widget=True))],
                tool_config=types.ToolConfig(retrieval_config=types.RetrievalConfig(
                    # Empire State Building, NY
                    lat_lng=types.LatLng(latitude=40.748817, longitude=-73.985428)
                )),
            ),
        )

        console.print("\n[bold green]Response:[/]")
        console.print(response.text)

        if response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            if meta.grounding_chunks:
                console.print("\n[bold yellow]Grounding Sources:[/]")
                for chunk in meta.grounding_chunks:
                    if chunk.maps:
                        console.print(f"- [link={chunk.maps.uri}]{chunk.maps.title}[/link]")
            
            if meta.google_maps_widget_context_token:
                console.print("\n[bold blue]Widget Token received![/]")

    except Exception as e:
        if "401" in str(e) and "API keys are not supported" in str(e):
            console.print("\n[bold red]Authentication Error:[/]")
            console.print("The API Key rejected the Maps Grounding request.")
            console.print("Common Causes:")
            console.print("1. Google Maps Platform API is not enabled on the Cloud Project.")
            console.print("2. Billing is not enabled (required for Grounding even on free tier).")
            console.print("3. This specific API feature requires OAuth instead of API Keys for your project settings.")
        else:
            console.print(f"[red]Error:[/]\n{e}")

if __name__ == "__main__":
    test_maps_grounding()
