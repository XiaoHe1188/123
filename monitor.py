import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

# 配置参数
API_URL = "http://zys-hr.com/server/examination/hrRecruitmentResults/list?state=2&pageNo=1&pageSize=7"  # 要监控的接口地址

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
        print(data["result"]["records"][0]["title"])
        # 检查是否有新的匹配消息
        for records in data["result"]["records"]:
            if "遵义市大数据集团有限公司" in records["title"] and "笔试" in records["title"] and len(records) > 0:
                return True, json.dumps(records["title"], ensure_ascii=False, indent=2)
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
        # 修复From头部格式 - 使用formataddr确保符合RFC标准
        # 格式为：(显示名称, 邮箱地址)
        msg['From'] = formataddr(("遵义市大数据笔试结果出来了！", EMAIL_FROM))
        msg['To'] = EMAIL_TO
        msg['Subject'] = Header('遵义市大数据集团有限公司笔试结果通知', 'utf-8')

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
        send_email_notification(f"{msg}")
