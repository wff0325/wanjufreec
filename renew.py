import requests
import os
import json
import base64
import time
import random
from datetime import datetime, timezone, timedelta

# ================= 核心配置 (已验证) =================
SERVER_ID = "1ed88a77-8513-43f9-9d1e-3a0db85b84b5"
ACTION_ID = "40f34f412fbff5791ab05264298fe5d6879efba201" 
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"

# 从 GitHub Secrets 获取
EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# 模拟不同的浏览器 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Edge/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

def send_tg_notification(content):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": content, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def run_task():
    if not EMAIL or not PASSWORD:
        print("❌ 错误: 未设置登录凭据")
        return

    # 随机选择一个浏览器标识
    current_ua = random.choice(USER_AGENTS)
    session = requests.Session()
    session.headers.update({"User-Agent": current_ua})

    print(f"📡 正在登录账号: {EMAIL}...")
    login_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json={"email": EMAIL, "password": PASSWORD}, headers=login_headers)
    
    if r_login.status_code != 200:
        send_tg_notification(f"❌ <b>续期登录失败</b>\n{r_login.text}")
        return
    
    # 模拟人登录后查看页面的随机等待 (5-15秒)
    wait_after_login = random.randint(5, 15)
    print(f"✅ 登录成功，模拟阅读页面 {wait_after_login} 秒...")
    time.sleep(wait_after_login)

    # 构造身份 Cookie
    auth_data = r_login.json()
    access_token = auth_data.get("access_token")
    cookie_dict = {
        "access_token": access_token,
        "refresh_token": auth_data.get("refresh_token"),
        "token_type": "bearer",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "user": auth_data.get("user")
    }
    cookie_val = f"base64-{base64.b64encode(json.dumps(cookie_dict).encode()).decode()}"
    session.cookies.set("sb-aeilbxxjgrnnqmtwnesh-auth-token", cookie_val, domain="freexcraft.com")

    # 模拟点击按钮前的短暂犹豫 (2-5秒)
    time.sleep(random.randint(2, 5))

    print(f"🛠️ 正在发送续期 Action...")
    action_headers = {
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "next-action": ACTION_ID,
        "referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}",
        "origin": "https://freexcraft.com"
    }
    action_body = f'["{SERVER_ID}"]'
    r_action = session.post(f"https://freexcraft.com/dashboard/server/{SERVER_ID}", 
                           data=action_body, headers=action_headers)

    if r_action.status_code != 200:
        send_tg_notification(f"❌ <b>续期 Action 失败</b>\n状态码: {r_action.status_code}")
        return

    # 等待数据库同步的随机时间 (4-8秒)
    wait_for_db = random.randint(4, 8)
    print(f"🎉 续期请求已发送，等待 {wait_for_db} 秒同步数据...")
    time.sleep(wait_for_db)

    # 获取最新状态
    info_headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    r_info = requests.get(f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*", headers=info_headers)
    
    if r_info.status_code == 200 and len(r_info.json()) > 0:
        data = r_info.json()[0]
        deadline_str = data.get('renewal_deadline')
        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        remaining = deadline - datetime.now(timezone.utc)
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        report = (
            f"✅ <b>FreeXCraft 自动续期成功</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🖥 <b>服务器:</b> <code>{data.get('name')}</code>\n"
            f"⏰ <b>剩余寿命:</b> <code>{hours}小时 {minutes}分钟</code>\n"
            f"📅 <b>过期时间:</b> <code>{(deadline + timedelta(hours=8)).strftime('%m-%d %H:%M')}</code>\n"
            f"🌐 <b>指纹:</b> <code>{current_ua.split(' ')[1]}</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🚀 <b>状态:</b> 自动守护中"
        )
        send_tg_notification(report)
        print("✅ 任务完成")
    else:
        send_tg_notification("✅ 续期已完成，但未能获取到最新时间戳。")

if __name__ == "__main__":
    run_task()
