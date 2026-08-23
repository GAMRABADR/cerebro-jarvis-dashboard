import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
import json
import time

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

def search_duckduckgo(query, max_results=4):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        res = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for a in soup.find_all("a", class_="result__url")[:max_results]:
            parent = a.find_parent("div", class_="result__body")
            title_tag = parent.find("a", class_="result__snippet") if parent else None
            title_main = parent.find("a", class_="result__a") if parent else None
            
            href = a.get("href", "")
            # Extract real target if redirected
            if "uddg=" in href:
                href = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                
            title = title_main.get_text(strip=True) if title_main else "Risultato Web"
            snippet = title_tag.get_text(strip=True) if title_tag else ""
            if href and not href.startswith("/"):
                results.append({
                    "title": title,
                    "url": href,
                    "snippet": snippet
                })
        return results
    except Exception as e:
        print(f"[DDG Search Error]: {e}")
        return []

def read_webpage(url, max_chars=3500):
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    try:
        if not url.startswith("http"):
            url = "https://" + url
        res = requests.get(url, headers=headers, timeout=9)
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Remove script, style, nav, footer tags
        for script in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            script.decompose()
            
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r'\s+', ' ', text).strip()
        title = soup.title.string if soup.title else url
        
        return {
            "status": "SUCCESS",
            "url": url,
            "title": title,
            "content": text[:max_chars],
            "char_count": len(text)
        }
    except Exception as e:
        return {"status": "ERROR", "url": url, "message": f"Errore lettura pagina: {str(e)}"}

def execute(params=None):
    params = params or {}
    url = params.get("url")
    query = params.get("query")
    mode = params.get("mode", "auto") # read_url | search | deep_research
    
    if url:
        res_page = read_webpage(url)
        return {
            "status": "SUCCESS",
            "mode": "read_url",
            "page_data": res_page,
            "message": f"Pagina '{res_page.get('title', url)}' letta con successo ({len(res_page.get('content', ''))} caratteri estratti)."
        }
        
    elif query:
        search_results = search_duckduckgo(query, max_results=4)
        page_summary = ""
        # If deep research, read the first organic result too
        if mode == "deep_research" and search_results:
            first_url = search_results[0]["url"]
            first_page = read_webpage(first_url, max_chars=2000)
            page_summary = first_page.get("content", "")
            
        return {
            "status": "SUCCESS",
            "mode": "search",
            "query": query,
            "results_count": len(search_results),
            "results": search_results,
            "deep_page_content": page_summary,
            "message": f"Ricerca completata: trovate {len(search_results)} fonti sul web per '{query}'."
        }
    else:
        return {"status": "ERROR", "message": "Fornire un 'url' da navigare o una 'query' da cercare."}

if __name__ == "__main__":
    print(execute({"query": "Unreal Engine 5.8 patch notes"}))
