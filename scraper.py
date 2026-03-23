import feedparser
import urllib.parse

feedparser.USER_AGENT = "Paper-Slave-Bot/1.0 (https://github.com/rayhuang2006/Paper-Slave)"

def fetch_arxiv_papers(query="cat:cs.LG OR cat:cs.CR", max_results=5):
    """從 arXiv API 抓取最新論文"""
    
    # 將查詢字串進行 URL 編碼 (把空格變成 %20 等)
    encoded_query = urllib.parse.quote(query)
    
    url = f"http://export.arxiv.org/api/query?search_query={encoded_query}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    feed = feedparser.parse(url)
    
    papers = []
    for entry in feed.entries:
        papers.append({
            "title": entry.title.replace('\n', ' '),
            "abstract": entry.summary.replace('\n', ' '),
            "link": entry.link
        })
    
    # 將結果格式化為容易讓 LLM 閱讀的字串
    formatted_data = ""
    for i, p in enumerate(papers, 1):
        formatted_data += f"Paper {i}:\nTitle: {p['title']}\nAbstract: {p['abstract']}\nLink: {p['link']}\n\n"
    
    return formatted_data