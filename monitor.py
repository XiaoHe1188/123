import requests
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置参数
API_URL = "https://zys-hr.com/server/examination/hrRecruitmentResults/list?state=2&pageNo=1&pageSize=7"  # 要监控的接口地址

# 邮箱配置（从环境变量获取）
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
EMAIL_FROM = os.getenv("EMAIL_FROM")  # 发件人QQ邮箱
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # QQ邮箱授权码
EMAIL_TO = os.getenv("EMAIL_TO")  # 收件人邮箱（可以和发件人相同）


# 测试
# EMAIL_FROM = "891481675@qq.com"  # 发件人QQ邮箱
# EMAIL_PASSWORD = "dqlpobglzdzpbeji"  # QQ邮箱授权码
# EMAIL_TO = "891481675@qq.com"  # 收件人邮箱（可以和发件人相同）

def create_session_with_retries():
    """创建带重试机制的requests会话"""
    session = requests.Session()
    # 配置重试策略
    retry_strategy = Retry(
        total=3,  # 总重试次数
        backoff_factor=1,  # 重试间隔时间（1秒, 2秒, 4秒...）
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
        allowed_methods=["GET"]  # 只对GET请求重试
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def check_api():
    try:
        session = create_session_with_retries()

        # 定义请求头（模拟浏览器访问）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive"
        }

        # 发送带请求头的GET请求
        response = session.get(API_URL, headers=headers, timeout=15)
        if response.status_code != 200:
            return False, f"接口状态异常，状态码: {response.status_code}"

        # 解析接口返回数据（根据实际接口格式调整）
        data = response.json()
        print(data["result"]["records"][0]["title"])
        # 检查是否有新的匹配消息
        for records in data["result"]["records"]:
            if "遵义市大数据集团有限公司" in records["title"] and "笔试成绩" in records["title"] and len(records) > 0:
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
