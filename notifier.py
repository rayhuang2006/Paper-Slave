import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email_report(report_content):
    """將報告透過 Email 寄出"""
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    receiver_email = os.getenv("EMAIL_RECEIVER")
    
    if not sender_email or sender_password == "your_app_password_here":
        print("\n" + "="*50)
        print("📝 [終端機預覽] 未設定 Email 憑證，以下為分析結果：")
        print("="*50 + "\n")
        print(report_content)
        print("\n" + "="*50)
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "📊 [Paper-Slave] 本週學術前沿情報雷達報告"

    msg.attach(MIMEText(report_content, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("✅ 報告已成功發送至 Email！")
    except Exception as e:
        print(f"❌ 寄信失敗: {e}")