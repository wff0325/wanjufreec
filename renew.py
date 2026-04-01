import requests
import os
import json
import base64
import time
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
# ===================================================

def send_tg_notification(content):
    """发送 Telegram 消息"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("⚠️ 未配置 Telegram 机器人，跳过推送。")
        return
    
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": content,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            print("🔔 Telegram 通知已发送")
        else:
            print(f"❌ TG 发送失败: {res.text}")
    except Exception as e:
        print(f"❌ TG 发送异常: {e}")

def run_task():
    if not EMAIL or not PASSWORD:
        print("❌ 错误: 请在 Secrets 中设置 FXC_EMAIL 和 FXC_PASS")
        return

    session = requests.Session()
    
    # 1. 登录 Supabase
    print(f"📡 正在登录账号: {EMAIL}...")
    login_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json={"email": EMAIL, "password": PASSWORD}, headers=login_headers)
    
    if r_login.status_code != 200:
        msg = f"❌ <b>FreeXCraft 登录失败</b>\n账号: {EMAIL}\n错误: {r_login.text}"
        send_tg_notification(msg)
        return
    
    auth_data = r_login.json()
    access_token = auth_data.get("access_token")
    
    # 2. 构造身份 Cookie
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

    # 3. 发送续期指令
    print(f"🛠️ 正在执行续期 Action...")
    action_headers = {
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "next-action": ACTION_ID,
        "referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
    }
    action_body = f'["{SERVER_ID}"]'
    r_action = session.post(f"https://freexcraft.com/dashboard/server/{SERVER_ID}", 
                           data=action_body, headers=action_headers)

    if r_action.status_code != 200:
        send_tg_notification(f"❌ <b>续期请求失败</b>\n状态码: {r_action.status_code}")
        return

    # 4. 获取最新状态并推送
    time.sleep(3) # 等待后端同步
    info_headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    r_info = requests.get(f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*", headers=info_headers)
    
    if r_info.status_code == 200 and len(r_info.json()) > 0:
        data = r_info.json()[0]
        name = data.get('name')
        deadline_str = data.get('renewal_deadline')
        
        # 计算剩余时间 (转换为北京时间显示更直观)
        deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        remaining = deadline - now
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        # 模拟网页“截图”样式的文字报告
        report = (
            f"✅ <b>FreeXCraft 自动续期成功</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🖥 <b>服务器名:</b> <code>{name}</code>\n"
            f"🆔 <b>服务器ID:</b> <code>{SERVER_ID[:8]}...</code>\n"
            f"⏰ <b>剩余寿命:</b> <code>{hours}小时 {minutes}分钟</code>\n"
            f"📅 <b>到期时间:</b> <code>{(deadline + timedelta(hours=8)).strftime('%m-%d %H:%M')} (CST)</code>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🚀 <b>状态:</b> 运行中 / 已满血"
        )
        send_tg_notification(report)
        print("🎉 续期成功并已发送通知")
    else:
        send_tg_notification("✅ 续期指令已发送，但无法获取详情。")

if __name__ == "__main__":
    run_task()
