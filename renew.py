import requests
import os
import json
import base64
import time
import random
import re
from datetime import datetime, timezone, timedelta

# ================= 核心配置 =================
SERVER_ID = "c2c11e40-1821-47c2-bd50-5651cdcbf268"
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"

# 默认保底 ID (你抓到的那一个)
CURRENT_ACTION_ID = "40f53a98e53e936c81bbae1afe242f83ecba099143"

EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def get_latest_action_id(session):
    """【黑科技】深度扫描 JS 块寻找最新的 Action ID"""
    print("🔍 启动深度扫描，尝试抓取最新的 Action ID...")
    try:
        url = f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
        res = session.get(url, timeout=15)
        
        # 1. 提取所有 JS 文件的路径
        # Next.js 文件的特征路径：/_next/static/chunks/...
        js_paths = re.findall(r'/_next/static/chunks/[^"]+\.js', res.text)
        
        # 2. 优先筛选含有 'app/dashboard' 或 'page' 关键字的脚本，Action ID 通常在这
        priority_chunks = [p for p in js_paths if 'page' in p or 'dashboard' in p]
        # 如果没搜到带关键字的，就扫所有的（最多扫前20个防止超时）
        scan_list = priority_chunks + [p for p in js_paths if p not in priority_chunks]
        
        print(f"🔎 发现 {len(js_paths)} 个 JS 块，正在深入分析前 {min(len(scan_list), 15)} 个核心块...")

        for js_path in scan_list[:15]:
            js_url = f"https://freexcraft.com{js_path}"
            js_res = session.get(js_url, timeout=10)
            if js_res.status_code == 200:
                # 匹配 40 位哈希值。Next.js 的 Action ID 通常跟在 specific 模式后面
                # 经过分析，续期的 ID 通常会出现在一段混淆代码中
                # 我们寻找符合特征的 ID
                ids = re.findall(r'[a-f0-9]{40}', js_res.text)
                if ids:
                    # 返回找到的第一个符合特征的（通常 40f 开头的是续期或核心操作）
                    for potential_id in ids:
                        # 这是一个简单的过滤逻辑，因为页面可能有多个 ID
                        if potential_id.startswith('40f'):
                            print(f"✨ 成功捕捉到动态 Action ID: {potential_id[:8]}...")
                            return potential_id
                            
    except Exception as e:
        print(f"⚠️ 动态抓取失败: {e}")
    
    print("📢 未能发现新 ID，回退使用预置 ID。")
    return CURRENT_ACTION_ID

def send_tg_notification(content):
    if not TG_BOT_TOKEN or not TG_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": content, "parse_mode": "HTML"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def parse_time(time_str):
    if not time_str: return None
    try:
        clean_ts = re.sub(r'(\.\d+)', lambda m: m.group(0)[:7].ljust(7, '0'), time_str)
        clean_ts = clean_ts.replace('Z', '+00:00')
        return datetime.fromisoformat(clean_ts)
    except:
        try:
            base_time = time_str.split('.')[0].split('+')[0].replace('Z', '')
            return datetime.strptime(base_time, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except: return None

def run_task():
    if not EMAIL or not PASSWORD:
        print("❌ 错误: 未设置登录凭据")
        return

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"})

    # 1. 登录
    print(f"📡 正在登录账号: {EMAIL}...")
    login_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json={"email": EMAIL, "password": PASSWORD}, headers=login_headers)
    
    if r_login.status_code != 200:
        print("❌ 登录失败")
        return
    
    auth_data = r_login.json()
    access_token = auth_data.get("access_token")
    
    # 2. 注入 Cookie
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

    # 3. 动态获取 ID
    # 必须在设置 Cookie 后执行，否则无法进入 dashboard
    action_id = get_latest_action_id(session)

    # 4. 执行续期
    time.sleep(random.randint(2, 5))
    print(f"🛠️ 正在发送续期 Action...")
    
    action_headers = {
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "next-action": action_id,
        "referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
    }
    r_action = session.post(f"https://freexcraft.com/dashboard/server/{SERVER_ID}", 
                           data=f'["{SERVER_ID}"]', headers=action_headers)

    if r_action.status_code != 200:
        print(f"❌ 续期失败: {r_action.status_code}")
        return

    print(f"🎉 续期请求发送成功，正在验证...")
    time.sleep(8)

    # 5. 获取结果并推送 TG
    info_headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    r_info = requests.get(f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*", headers=info_headers)
    
    if r_info.status_code == 200 and len(r_info.json()) > 0:
        data = r_info.json()[0]
        deadline = parse_time(data.get('renewal_deadline'))
        if deadline:
            remaining = deadline - datetime.now(timezone.utc)
            report = (
                f"✅ <b>FreeXCraft 自动续期成功</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🖥 <b>服务器:</b> <code>{data.get('name')}</code>\n"
                f"⏰ <b>剩余寿命:</b> <code>{int(remaining.total_seconds() // 3600)}小时</code>\n"
                f"📅 <b>到期时间:</b> <code>{(deadline + timedelta(hours=8)).strftime('%m-%d %H:%M')}</code>\n"
                f"🆔 <b>动态ID:</b> <code>{action_id[:8]}...</code>\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            send_tg_notification(report)
            print("✅ 任务完成")

if __name__ == "__main__":
    run_task()
