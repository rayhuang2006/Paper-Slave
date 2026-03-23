import os
import datetime # 👈 新增這個來獲取今天的日期
from dotenv import load_dotenv
from scraper import fetch_arxiv_papers
from llm_engine import analyze_papers
from notifier import send_email_report

def main():
    print("🚀 啟動 Paper-Slave 學術雷達...")
    load_dotenv()
    
    print("⏳ 正在從 arXiv 抓取最新論文 (cs.LG, cs.CR)...")
    paper_data = fetch_arxiv_papers(max_results=5)
    
    if not paper_data.strip():
        print("❌ 找不到論文資料，程式結束。")
        return
        
    print("🧠 正在將資料送交 Gemini 2.5 Flash 進行評分與摘要...")
    report = analyze_papers(paper_data)
    
    # ======== 【W4 新增：長期記憶落地 (存檔)】 ========
    print("💾 正在將本週報告寫入歷史檔案庫...")
    os.makedirs("archive", exist_ok=True) # 如果沒有 archive 資料夾，就自動建一個
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"archive/report_{today_str}.md"
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 📅 {today_str} 學術前沿報告\n\n")
        f.write(report)
    print(f"✅ 報告已成功歸檔至 {filename}")
    # ==================================================
    
    print("📨 正在準備發送報告...")
    send_email_report(report)
    
    print("🎉 任務完成！奴工退下。")

if __name__ == "__main__":
    main()