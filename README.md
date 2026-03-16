# Paper-Slave (學術前沿情報雷達) 

這是一個基於 Python 與 Gemini 2.5 Flash 構建的自動化學術情報抓取與總結 Agent。它能自動從 arXiv 爬取最新論文，過濾低價值內容，並將高影響力論文的核心貢獻提煉成一句話摘要，最後透過 Email 推播給使用者。

## 功能特色
- **自動化爬蟲**：串接 arXiv API，精準抓取特定領域 (如 cs.LG, cs.CR) 最新文獻。
- **LLM 智慧總結**：介接 Google GenAI SDK (Gemini 2.5 Flash)，自動進行 1-10 分學術評分，並生成 50 字內繁體中文摘要。
- **Prompt Injection 系統級防護**：內建安全結界，能有效辨識並攔截摘要中潛藏的惡意指令（已通過紅隊對抗性測試）。
- **Markdown 推播**：自動生成排版精美的 Markdown 報表，並透過 SMTP 發送 Email。

## 快速啟動
1. 複製專案並安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   ```

2. 在根目錄建立 `.env` 檔案，並填入以下資訊：
    ```env
    GEMINI_API_KEY=your_gemini_api_key
    EMAIL_SENDER=your_email@gmail.com
    EMAIL_PASSWORD=your_app_password
    EMAIL_RECEIVER=your_email@gmail.com
    ```

3. 執行主程式：
    ```bash
    python3 main.py
    ```
