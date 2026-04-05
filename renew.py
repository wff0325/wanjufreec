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

# 默认保底 ID
FALLBACK_ACTION_ID = "40f53a98e53e936c81bbae1afe242f83ecba099143"

EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def get_latest_action_id(session):
    """【增强版】全量扫描并识别最可能的续期 Action ID"""
    print("🔍 启动增强扫描...")
    try:
        url = f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
        res = session.get(url, timeout=15)
        
        # 1. 先从主页面尝试提取隐藏的 Action 定义
        # Next.js 偶尔会将 Action ID 存在 self.__next_f.push 的字符串里
        html_ids = re.findall(r'[a-f0-9]{40}', res.text)
        if html_ids:
            # 排除掉常用的公共 Hash
            likely_id = [i for i in html_ids if i != "0000000000000000000000000000000000000000"]
            if likely_id:
                print(f"✨ 在 HTML 源码中发现 ID: {likely_id[0][:8]}...")
                return likely_id[0]

        # 2. 深入 JS 块分析
        js_paths = re.findall(r'/_next/static/chunks/[^"]+\.js', res.text)
        # 优先级：page -> layout -> 其他
        sorted_chunks = sorted(js_paths, key=lambda x: ('page' not in x, 'layout' not in x))
        
        print(f"🔎 正在分析核心 JS 块 (共 {len(js_paths)} 个)...")
        for js_path in sorted_chunks[:20]: # 增加扫描深度到 20 个
            js_res = session.get(f"https://freexcraft.com{js_path}", timeout=10)
            if js_res.status_code == 200:
                # 寻找 40 位哈希
                ids = re.findall(r'[a-f0-9]{40}', js_res.text)
                if ids:
                    # 过滤掉一些明显的静态资源哈希（如果长度正好 40 的话）
                    # 续期 ID 通常在 JS 里作为对象的 key 或 value 出现
                    for potential in ids:
                        # 只要找到一个 40 位哈希就返回，这是目前最稳妥的自动策略
                        print(f"🎯 从 JS 块 [{js_path.split('/')[-1]}] 捕获 ID: {potential[:8]}...")
                        return potential
                            
    except Exception as e:
        print(f"⚠️ 扫描异常: {e}")
    
    print("📢 自动扫描未果，使用保底 ID 尝试...")
    return FALLBACK_ACTION_ID

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
        print("❌ 错误: 未设置凭据")
        return

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"})

    # 1. 登录
    print(f"📡 登录账号: {EMAIL}...")
    login_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json={"email": EMAIL, "password": PASSWORD}, headers=login_headers)
    
    if r_login.status_code != 200:
        print("❌ 登录失败")
        return
    
    auth_data = r_login.json()
    access_token = auth_data.get("access_token")
    
    # 2. 设置 Cookie
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

    # 3. 抓取 Action ID
    action_id = get_latest_action_id(session)

    # 4. 执行续期
    time.sleep(5)
    print(f"🛠️ 正在执行续期...")
    
    action_headers = {
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "next-action": action_id,
        "referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
    }
    r_action = session.post(f"https://freexcraft.com/dashboard/server/{SERVER_ID}", 
                           data=f'["{SERVER_ID}"]', headers=action_headers)

    if r_action.status_code != 200:
        print(f"❌ 失败: {r_action.status_code}")
        send_tg_notification(f"❌ <b>续期失败</b>\nAction ID 可能已失效。")
        return

    print(f"🎉 续期指令已发送，正在验证数据...")
    time.sleep(10)

    # 5. 验证并推送
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
                f"🆔 <b>使用的ID:</b> <code>{action_id[:8]}...</code>\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            send_tg_notification(report)
            print("✅ 任务完成")
