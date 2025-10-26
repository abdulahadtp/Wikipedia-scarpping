from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI(title="Country Wikipedia Outline API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Country Wikipedia Outline API",
        "usage": "GET /api/outline?country=<country_name>",
        "example": "/api/outline?country=Vanuatu"
    }

@app.get("/api/outline")
def get_country_outline(country: str = Query(..., description="Name of the country")):
    try:
        # Construct Wikipedia URL
        encoded_country = urllib.parse.quote(country.replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/wiki/{encoded_country}"
        
        # Fetch Wikipedia page
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(wiki_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"Could not fetch page for '{country}'"}
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.find('div', {'id': 'mw-content-text'})
        
        if not content:
            return {"error": "Could not find content"}
        
        # Extract headings
        headings = content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        # Generate Markdown
        markdown_lines = ["## Contents", ""]
        
        # Add main title
        title_tag = soup.find('h1', {'id': 'firstHeading'})
        if title_tag:
            markdown_lines.append(f"# {title_tag.get_text().strip()}")
            markdown_lines.append("")
        
        # Process headings
        for heading in headings:
            level = int(heading.name[1])
            text = heading.get_text().strip()
            
            # Clean text
            text = text.replace('[edit]', '').strip()
            
            # Skip navigation headings
            skip = ['Contents', 'Navigation menu', 'Personal tools', 
                   'Namespaces', 'Views', 'Search', 'Tools', 'Languages']
            
            if text and text not in skip:
                markdown_lines.append('#' * level + ' ' + text)
                markdown_lines.append("")
        
        markdown_output = '\n'.join(markdown_lines)
        
        return {
            "country": country,
            "url": wiki_url,
            "outline": markdown_output
        }
        
    except Exception as e:
        return {"error": str(e)}
