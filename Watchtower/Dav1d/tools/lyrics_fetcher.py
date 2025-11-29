import argparse
import json
import sys
import re
from urllib.request import Request, urlopen
from urllib.error import URLError

def get_azlyrics_content(url):
    """
    Fetches and extracts title and lyrics specifically for AZLyrics.
    Uses regex because AZLyrics HTML structure is simple enough for it 
    and avoids complex HTMLParser state for their specific layout.
    """
    print(f"Fetching: {url}", file=sys.stderr)
    try:
        # User-Agent is critical for AZLyrics
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        req = Request(url, headers=headers)
        with urlopen(req, timeout=10) as response:
            charset = response.headers.get_content_charset() or 'utf-8'
            html = response.read().decode(charset, errors='ignore')
            
            # Extract Title: <h1>"Title" lyrics</h1> or similar
            # AZLyrics title format: <div class="lyricsh"><h2><b>"Song Title" lyrics</b></h2></div>
            # Or simply look for the header
            title_match = re.search(r'<b>"(.*?)" lyrics</b>', html)
            if not title_match:
                # Fallback
                title_match = re.search(r'<h1>(.*?) lyrics</h1>', html)
            
            title = title_match.group(1) if title_match else "Unknown Title"
            
            # Extract Lyrics: Look for the comment they always include
            start_marker = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our licensing agreement. Sorry about that. -->'
            end_marker = '</div>'
            
            if start_marker in html:
                start_idx = html.find(start_marker) + len(start_marker)
                end_idx = html.find(end_marker, start_idx)
                lyrics_raw = html[start_idx:end_idx].strip()
                
                # Clean up <br> tags
                lyrics_clean = re.sub(r'<br\s*/?>', '\n', lyrics_raw)
                # Remove other tags if any
                lyrics_clean = re.sub(r'<[^>]+>', '', lyrics_clean)
                # Decode entities
                import html as html_lib
                lyrics_clean = html_lib.unescape(lyrics_clean).strip()
                
                return title, lyrics_clean
            else:
                print(f"Warning: Lyrics start marker not found in {url}", file=sys.stderr)
                return None, None

    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None, None

def main():
    parser = argparse.ArgumentParser(description="Fetch Chief Keef lyrics from AZLyrics.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('urls', nargs='*', help="URLs to fetch")
    group.add_argument('-f', '--file', dest='url_file', help="File with URLs")
    parser.add_argument('-o', '--output', required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    all_urls = []
    if args.url_file:
        try:
            with open(args.url_file, 'r', encoding='utf-8') as f:
                all_urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            sys.exit(f"File not found: {args.url_file}")
    else:
        all_urls = args.urls
        
    collection = {}
    
    for url in all_urls:
        title, lyrics = get_azlyrics_content(url)
        if title and lyrics:
            collection[title] = lyrics
            print(f"✅ Parsed: {title}", file=sys.stderr)
        else:
            print(f"❌ Failed: {url}", file=sys.stderr)
            
    if collection:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(collection, f, indent=4, ensure_ascii=False)
        print(f"Saved {len(collection)} songs to {args.output}")
    else:
        print("No lyrics extracted.")

if __name__ == "__main__":
    main()