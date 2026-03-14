"""
CMS portal scraper — fetches live news and page text.
"""
import feedparser
import requests
from bs4 import BeautifulSoup

CMS_RSS_FEEDS = [
    "https://www.cms.gov/newsroom/rss/resources",
    "https://www.cms.gov/newsroom/rss/press-releases",
]

CMS_HCPCS_URL = (
    "https://www.cms.gov/medicare/coding-billing/"
    "healthcare-common-procedure-system/quarterly-update"
)


def fetch_cms_news(max_items: int = 10) -> list:
    """Fetch latest CMS news from RSS feeds."""
    articles = []
    for url in CMS_RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_items]:
                articles.append({
                    "title":   entry.get("title", ""),
                    "summary": entry.get("summary", "")[:300],
                    "link":    entry.get("link", ""),
                    "date":    entry.get("published", ""),
                    "source":  url,
                })
        except Exception:
            continue
    return articles


def fetch_page_text(url: str, max_chars: int = 8000) -> str:
    """
    Fetch a CMS webpage and return its plain text.
    Strips navigation, headers, footers automatically.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; HealthGuardBot/1.0)"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Remove navigation and boilerplate
    for tag in soup(["nav", "header", "footer", "script", "style", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text[:max_chars]


def search_cms_codes(code: str) -> dict:
    """
    Try to fetch information about a specific CPT/HCPCS code from CMS.
    Returns whatever text is available.
    """
    url = f"https://www.cms.gov/medicare/physician-fee-schedule/search?keyword={code}"
    try:
        text = fetch_page_text(url, max_chars=3000)
        return {"code": code, "source": url, "text": text}
    except Exception as e:
        return {"code": code, "source": url, "text": "", "error": str(e)}
