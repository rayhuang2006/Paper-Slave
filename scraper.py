import arxiv

def fetch_arxiv_papers(query="cat:cs.LG OR cat:cs.CR", max_results=15):
    """使用官方 arxiv SDK 抓取最新論文，內建防 429 封鎖機制"""
    
    print(f"🔗 [Debug] 啟動 arXiv 官方 SDK 抓取 (查詢: {query})...")
    
    try:
        # 1. 建立 Client，設定每次請求延遲 3 秒，最多重試 3 次，完美避開 429
        client = arxiv.Client(
            page_size=max_results,
            delay_seconds=3,
            num_retries=3
        )
        
        # [MVP 驗證] 將原本侷限在資工領域的 search_query 替換為跨域組合
        # 新增：stat.ML (統計機器學習), eess.SP (訊號處理), math.OC (最佳化與控制)
        search = arxiv.Search(
            query="cat:cs.LG OR cat:cs.CR OR cat:stat.ML OR cat:eess.SP OR cat:math.OC",
            max_results=max_results, # 保持原本的抓取數量即可
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        # 3. 執行搜尋並格式化
        formatted_data = ""
        results = list(client.results(search))
        
        if not results:
            print("⚠️ [Debug] 成功連線，但回傳 0 筆結果。")
            return ""
            
        for i, paper in enumerate(results, 1):
            # 把摘要裡的換行符號拿掉，讓 LLM 更好讀
            clean_abstract = paper.summary.replace('\n', ' ')
            formatted_data += f"Paper {i}:\nTitle: {paper.title}\nAbstract: {clean_abstract}\nLink: {paper.entry_id}\n\n"
            
        return formatted_data
        
    except Exception as e:
        print(f"❌ [Debug] 抓取發生錯誤: {e}")
        return ""