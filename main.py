import os
import json
import datetime
from dotenv import load_dotenv
from scraper import fetch_arxiv_papers
from llm_engine import analyze_papers_with_routing
from notifier import send_email_report

def main():
    print("🚀 啟動 Paper-Slave 學術雷達 (企業級 Multi-Agent 版)...")
    load_dotenv()
    
    # 1. 擴大抓取範圍，讓 Agent A 發揮過濾價值
    print("⏳ 正在從 arXiv 抓取最新 15 篇論文 (cs.LG, cs.CR)...")
    paper_data = fetch_arxiv_papers(max_results=15)
    
    if not paper_data.strip():
        print("❌ 找不到論文資料，程式結束。")
        return
        
    os.makedirs("archive", exist_ok=True)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # ==========================================
    # 📌 產線一：Pro 方案 (深度解析與 Email 推播)
    # ==========================================
    print("\n" + "="*50)
    print("🏭 啟動 Pro 產線：摘要與方向建議...")
    pro_report = analyze_papers_with_routing(paper_data, user_tier="Pro")
    
    md_filename = f"archive/report_{today_str}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(f"# 📅 {today_str} 學術前沿報告 (Pro Edition)\n\n")
        f.write(pro_report)
    print(f"✅ Pro 報告已成功歸檔至 {md_filename}")
    
    print("📨 正在發送 Pro 方案週報至 Email...")
    send_email_report(pro_report)
    
    # ==========================================
    # 📌 產線二：Ultra 方案 (跨域知識圖譜 JSON 落地)
    # ==========================================
    print("\n" + "="*50)
    print("🌌 啟動 Ultra 產線：萃取隱藏同構性...")
    ultra_json_str = analyze_papers_with_routing(paper_data, user_tier="Ultra")
    
    # 將 JSON 統一命名為 report_latest.json，方便前端網頁固定抓取
    json_filename = "archive/report_latest.json"
    
    # 確保寫入的是乾淨的 JSON 格式
    try:
        # 測試看看 Gemini 吐出來的是不是合法 JSON
        json_data = json.loads(ultra_json_str) 
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Ultra 知識圖譜已成功歸檔至 {json_filename}")
    except json.JSONDecodeError:
        print("⚠️ 警告：Agent C 輸出的不是標準 JSON 格式，強制寫入原始字串...")
        with open(json_filename, "w", encoding="utf-8") as f:
            f.write(ultra_json_str)
            
    print("\n🎉 多代理管線執行完畢！奴工退下。")

if __name__ == "__main__":
    main()