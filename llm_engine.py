import os
from google import genai
from google.genai import types
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

def analyze_papers(paper_data):
    """呼叫 Gemini API 進行論文分析"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return "⚠️ 系統提示: 請先在 .env 檔案中設定 GEMINI_API_KEY，否則大腦無法運作。"

    client = genai.Client(api_key=api_key)
    user_prompt = USER_PROMPT_TEMPLATE.format(paper_data=paper_data)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2, # 降低溫度讓輸出格式更穩定、嚴謹
            ),
        )
        return response.text
    except Exception as e:
        return f"❌ LLM 分析過程中發生錯誤: {e}"