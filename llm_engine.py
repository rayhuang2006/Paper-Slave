import os
import json
from groq import Groq
from prompts import (
    AGENT_A_SYSTEM, AGENT_A_USER,
    AGENT_B_SYSTEM, AGENT_B_USER,
    AGENT_C_SYSTEM, AGENT_C_USER
)

def analyze_papers_with_routing(paper_data, user_tier="Free"):
    """
    動態 LLM 路由器 (Dynamic LLM Router)
    根據使用者的方案 (Free, Pro, Ultra) 啟動不同深度的 Agent 管線。
    """
    if user_tier == "Free":
        return "Free 方案僅提供原始論文摘要推播，請升級以解鎖 AI 深度解析。"

    # ==========================================
    # 階段 1：Agent A (初篩小腦) - 呼叫 Groq API
    # ==========================================
    print("🧠 [Agent A] 啟動：使用 Groq (Llama-3) 進行極速初篩...")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return "⚠️ 系統提示: 找不到 GROQ_API_KEY，大腦管線無法啟動。"
    
    groq_client = Groq(api_key=groq_api_key)
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": AGENT_A_SYSTEM},
                {"role": "user", "content": AGENT_A_USER.format(paper_data=paper_data)}
            ],
            temperature=0.1,
        )
        filtered_papers = completion.choices[0].message.content
        print(f"✅ [Agent A] 初篩完成，保留以下論文：\n{filtered_papers}\n")
    except Exception as e:
        return f"❌ Agent A (Groq) 執行失敗: {e}"

    # 如果初篩結果是空的，就不用浪費 Gemini 的錢了
    # [Hotfix] 改用精確比對避免論文標題含「無」字被誤殺
    if filtered_papers.strip() == "無" or not filtered_papers.strip():
        return "本週無具備重大突破之論文。"

    # ==========================================
    # 階段 2：大腦深加工 (全面切換至 Groq 引擎)
    # ==========================================
    if user_tier == "Pro":
        print("🧠 [Agent B] 啟動：使用 Groq (Llama-3.3-70B) 進行 Pro 級深度解析...")
        prompt = AGENT_B_USER.format(filtered_papers=filtered_papers)
        system_instruction = AGENT_B_SYSTEM
        
    elif user_tier == "Ultra":
        print("🌌 [Agent C] 啟動：使用 Groq (Llama-3.3-70B) 進行 Ultra 級跨域圖譜建構...")
        prompt = AGENT_C_USER.format(filtered_papers=filtered_papers)
        # 強烈要求 JSON 格式，排除任何額外文字或標記
        system_instruction = AGENT_C_SYSTEM + "\n\nIMPORTANT: You must output a valid JSON string ONLY. NO markdown code blocks (e.g., ```json), NO headers, NO conversational filler. Just the raw JSON object."
        
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            # 強制 Groq 進行 JSON 模式 (如果支援的話)
            response_format={"type": "json_object"} if user_tier == "Ultra" else None
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ 深度大腦 (Groq-Llama3) 執行失敗: {e}"