import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import markdown  # 👈 新增這行，載入翻譯蒟蒻

def send_email_report(report_content, receivers):
    """將報告透過 Email 寄出，並利用迴圈 (BCC) 發送給多個用戶"""
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or sender_password == "your_app_password_here":
        print("\n" + "="*50)
        print("📝 [終端機預覽] 未設定 Email 憑證，以下為分析結果：")
        print("="*50 + "\n")
        print(report_content)
        print("\n" + "="*50)
        return

    if not receivers:
        print("⚠️ 沒有接收者 Email，跳過發信程序。")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    # 將自己的信箱設為 To，真正的名單由 sendmail 以 BCC 方式送出
    msg['To'] = sender_email
    msg['Subject'] = "📊 [Paper-Slave] 本週學術前沿情報雷達報告"

    # 🪄 魔法發生在這裡：把 Markdown 轉成漂漂亮亮的 HTML
    html_content = markdown.markdown(report_content)
    
    # 幫它加上一點基礎的 HTML 骨架，讓信件排版更乾淨
    full_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        {html_content}
      </body>
    </html>
    """

    # ⚠️ 注意這裡！我們把 'plain' 改成了 'html'
    msg.attach(MIMEText(full_html, 'html', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        # sendmail 支援傳入 list 作為收件名單，底層會自動透過 BCC 群發
        server.sendmail(sender_email, receivers, text)
        server.quit()
        print(f"✅ 報告已成功轉換為 HTML 並發送至 {len(receivers)} 個 Email 信箱！")
    except Exception as e:
        print(f"❌ 寄信失敗: {e}")