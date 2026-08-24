import requests
import re
import urllib.parse

def scrape_url_clean(url, use_jina=True):
    if not url.startswith("http"):
        url = "https://" + url
    
    # 1. Jina Reader AI Proxy (< 0.5s Clean Markdown)
    if use_jina:
        try:
            jina_url = f"https://r.jina.ai/{url}"
            r = requests.get(jina_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code == 200 and len(r.text) > 100:
                clean_md = r.text[:6000]
                return {
                    "status": "SUCCESS",
                    "url": url,
                    "engine": "Jina AI Markdown Parser",
                    "content_length": len(r.text),
                    "markdown": clean_md
                }
        except Exception as e:
            pass

    # 2. Direct HTTP Fallback
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=8)
        text = re.sub(r'<script.*?</script>', '', r.text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()[:4000]
        return {
            "status": "SUCCESS",
            "url": url,
            "engine": "Direct Fallback Scraper",
            "content_length": len(text),
            "markdown": text
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def execute(params=None):
    params = params or {}
    url = params.get("url", "https://news.ycombinator.com")
    return scrape_url_clean(url, params.get("use_jina", True))

if __name__ == "__main__":
    print(execute({"url": "https://en.wikipedia.org/wiki/Unreal_Engine"}))
