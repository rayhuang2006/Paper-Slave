import os
import json
import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

from scraper import fetch_arxiv_papers
from llm_engine import analyze_papers_with_routing
from notifier import send_email_report

def get_firestore_client():
    """ 初始化並回傳 Firebase Firestore 客戶端 """
    if not firebase_admin._apps:
        # 1. 優先檢查環境變數 FIREBASE_CRED_JSON 是否有值
        cred_json_str = os.getenv("FIREBASE_CRED_JSON")
        if cred_json_str:
            try:
                cred_dict = json.loads(cred_json_str)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("✅ 成功透過環境變數 (JSON) 初始化 Firebase 連線。")
            except Exception as e:
                print(f"⚠️ 解析 FIREBASE_CRED_JSON 發生錯誤: {e}")
                # 錯誤時繼續往下嘗試本機檔案驗證
        
        # 2. 如果上一步尚未成功初始化 apps，尋找本機憑證檔案
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CRED_PATH", "serviceAccountKey.json")
            try:
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("✅ 成功使用本機憑證初始化 Firebase 連線。")
            except Exception as e:
                print(f"⚠️ 無法透過 {cred_path} 初始化 Firebase，使用預設驗證。原因: {e}")
                # 在某些雲端環境（如 GCP）可運用預設憑證
                firebase_admin.initialize_app()
                
    return firestore.client()

def fetch_active_subscribers(db):
    """ 從 Firestore 撈取所有 Pro 與 Ultra 用戶清單以及他們的偏好領域 """
    print("🔍 正在從 Firestore 撈取付費用戶名單庫...")
    users_ref = db.collection("users")
    
    # 使用 in 查詢來獲取所有付費 tier 的用戶
    query = users_ref.where("tier", "in", ["Pro", "Ultra"])
    docs = query.stream()
    
    subscribers = []
    all_preferences = set()
    
    for doc in docs:
        data = doc.to_dict()
        email = data.get("email")
        tier = data.get("tier")
        prefs = data.get("domain_preferences", [])
        
        if email:
            subscribers.append({
                "email": email,
                "tier": tier,
                "domain_preferences": prefs
            })
            for pref in prefs:
                all_preferences.add(pref)
                
    return subscribers, list(all_preferences)

def main():
    print("🚀 啟動 Paper-Slave 學術雷達 (企業級 Multi-Agent 版)...")
    load_dotenv()
    
    # --- 新增: 連線 Firebase 並動態撈取用戶與領域 ---
    db = get_firestore_client()
    subscribers, all_preferences = fetch_active_subscribers(db)
    
    if not subscribers:
        print("🤷‍♂️ 目前沒有 Pro 或 Ultra 用戶，程式結束。")
        return
        
    print(f"👥 找到 {len(subscribers)} 位付費用戶。")
    print(f"🎯 彙整後的感興趣領域：{all_preferences}")
    
    # 組合 query，如果沒有偏好則退回預設值
    if all_preferences:
        arxiv_query = " OR ".join([f"cat:{pref}" for pref in all_preferences])
    else:
        arxiv_query = "cat:cs.LG OR cat:cs.CR"
        
    # 1. 根據動態組合的條件，擴大抓取範圍
    print(f"⏳ 正在從 arXiv 抓取最新 15 篇論文 (查詢字串: {arxiv_query})...")
    paper_data = fetch_arxiv_papers(query=arxiv_query, max_results=15)
    
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
    
    # [Hotfix] 錯誤阻斷機制：若 LLM 發生錯誤或初篩發現無論文，則中斷後續歸檔與寄信
    if pro_report.startswith("❌") or pro_report.startswith("⚠️") or "本週無具備重大突破之論文" in pro_report:
        print(f"\n🛑 管線安全中斷: {pro_report}")
        return
    
    md_filename = f"archive/report_{today_str}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(f"# 📅 {today_str} 學術前沿報告 (Pro Edition)\n\n")
        f.write(pro_report)
    print(f"✅ Pro 報告已成功歸檔至 {md_filename}")
    
    print("📨 正在發送 Pro 方案週報至 Email...")
    # 將找到的用戶 Emails 抽取成名單
    target_emails = [u["email"] for u in subscribers]
    send_email_report(pro_report, target_emails)
    
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