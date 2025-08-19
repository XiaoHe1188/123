import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 配置参数
API_URL = "https://your-api-url.com"  # 要监控的接口地址

# 邮箱配置（从环境变量获取）
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
EMAIL_FROM = os.getenv("EMAIL_FROM")  # 发件人QQ邮箱
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # QQ邮箱授权码
EMAIL_TO = os.getenv("EMAIL_TO")  # 收件人邮箱（可以和发件人相同）


def check_api():
    try:
        response = requests.get(API_URL, timeout=10)
        if response.status_code != 200:
            return False, f"接口状态异常，状态码: {response.status_code}"

        # 解析接口返回数据（根据实际接口格式调整）
        data = response.json()
        # 检查是否有新的匹配消息
        if "遵义市大数据集团有限公司2025年公开招聘工作人员笔试成绩" in data and len(data["result"]) > 0:
            return True, json.dumps(data["result"], ensure_ascii=False, indent=2)
        else:
            return False, "暂无新匹配消息"

    except Exception as e:
        return False, f"接口请求失败: {str(e)}"


def send_email_notification(message):
    if not all([EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO]):
        print("邮箱配置不完整，跳过通知")
        return

    try:
        # 构建邮件内容
        msg = MIMEText(message, 'plain', 'utf-8')
        msg['From'] = Header(f"接口监控通知 <{EMAIL_FROM}>", 'utf-8')
        msg['To'] = Header(EMAIL_TO, 'utf-8')
        msg['Subject'] = Header('检测到新的匹配消息', 'utf-8')

        # 连接SMTP服务器并发送邮件
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # 启用TLS加密
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO.split(','), msg.as_string())
        server.quit()

        print("邮件通知发送成功")
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")


if __name__ == "__main__":
    success, msg = check_api()
    print(f"监控结果: {msg}")
    if success:  # 只有检测到新消息时才发送通知
        send_email_notification(f"检测到新匹配消息：\n{msg}")
