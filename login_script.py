from playwright.sync_api import sync_playwright
import os
import requests

def send_pushplus_message(message):
    token = os.environ.get('PUSHPLUS_TOKEN')
    if not token:
        print("未设置 PUSHPLUS_TOKEN 环境变量")
        return {"error": "token_missing"}

    url = "https://www.pushplus.plus/send"
    payload = {
        "token": token,
        "title": "WEBHOST 登录状态通知",
        "content": message,
        "template": "markdown"
    }
    response = requests.post(url, json=payload)
    return response.json()

def login_webhost(email, password):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()

        # 访问登录页面
        page.goto("https://client.webhostmost.com/login")

        # 输入邮箱和密码
        page.get_by_placeholder("Enter email").fill(email)
        page.get_by_placeholder("Password").fill(password)

        # 点击登录按钮
        page.get_by_role("button", name="Login").click()

        try:
            # 尝试等待错误提示
            error_message = page.wait_for_selector('.MuiAlert-message', timeout=5000)
            error_text = error_message.inner_text()
            return f"账号 `{email}` 登录失败: {error_text}"
        except:
            # 未出现错误提示，判断是否成功跳转
            try:
                page.wait_for_url("https://client.webhostmost.com/clientarea.php", timeout=5000)
                return f"账号 `{email}` 登录成功 ✅"
            except:
                return f"账号 `{email}` 登录失败: 未跳转到仪表板页面 ❌"
        finally:
            browser.close()

if __name__ == "__main__":
    accounts_raw = os.environ.get('WEBHOST')
    if not accounts_raw:
        error_message = "未配置任何 WEBHOST 账号"
        send_pushplus_message(error_message)
        print(error_message)
        exit()

    accounts = accounts_raw.strip().split()
    login_statuses = []

    for account in accounts:
        try:
            email, password = account.split(':')
            status = login_webhost(email, password)
            login_statuses.append(status)
            print(status)
        except ValueError:
            login_statuses.append(f"账号格式错误: `{account}`，请使用 email:password 格式")
    
    if login_statuses:
        message = "### WEBHOST 登录状态结果\n\n" + "\n\n".join(login_statuses)
        result = send_pushplus_message(message)
        print("消息已发送到 PushPlus:", result)
