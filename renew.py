import requests
import os
import json
import base64
import time

# ================= 核心配置 =================
SERVER_ID = "1ed88a77-8513-43f9-9d1e-3a0db85b84b5"
ACTION_ID = "40f34f412fbff5791ab05264298fe5d6879efba201" # 刚才抓到的 next-action
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"

EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
# ==========================================

def run_task():
    if not EMAIL or not PASSWORD:
        print("❌ 请设置环境变量 FXC_EMAIL 和 FXC_PASS")
        return

    session = requests.Session()
    
    # 1. 登录 Supabase 获取 Token
    print(f"📡 正在尝试登录账号: {EMAIL}...")
    login_headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    login_data = {"email": EMAIL, "password": PASSWORD}
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json=login_data, headers=login_headers)
    
    if r_login.status_code != 200:
        print(f"❌ 登录失败: {r_login.text}")
        return
    
    auth_data = r_login.json()
    access_token = auth_data.get("access_token")
    refresh_token = auth_data.get("refresh_token")
    print("✅ 登录成功，正在构造身份 Cookie...")

    # 2. 构造 Next.js 所需的 base64 身份 Cookie
    # 格式参考抓包：base64-{"access_token":"...","refresh_token":"..."}
    cookie_dict = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "user": auth_data.get("user")
    }
    cookie_json = json.dumps(cookie_dict)
    cookie_b64 = base64.b64encode(cookie_json.encode()).decode()
    cookie_val = f"base64-{cookie_b64}"
    
    # 将 Cookie 放入 session
    cookie_name = "sb-aeilbxxjgrnnqmtwnesh-auth-token"
    session.cookies.set(cookie_name, cookie_val, domain="freexcraft.com")

    # 3. 发送 Next.js Server Action 请求
    print(f"🛠️ 正在发送续期 Action (ID: {ACTION_ID[:8]}...)")
    
    action_headers = {
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "next-action": ACTION_ID,
        "origin": "https://freexcraft.com",
        "referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Next.js Server Action 的 Body 通常是一个包含参数的数组
    # 根据 content-length: 40 推测，body 就是包含服务器 ID 的数组
    action_body = f'["{SERVER_ID}"]'
    
    action_url = f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
    r_action = session.post(action_url, data=action_body, headers=action_headers)

    if r_action.status_code == 200:
        print("🎉 续期请求已成功发送！服务器应该已续杯。")
        # 打印部分响应内容以供调试（Next.js 的响应通常是乱码一样的流数据）
        print(f"📄 响应预览: {r_action.text[:100]}")
    else:
        print(f"❌ Action 执行失败 ({r_action.status_code}): {r_action.text}")

    # 4. 验证结果
    print("\n📊 正在查询最新过期时间...")
    info_headers = {"apikey": SUPABASE_ANON_KEY, "Authorization": f"Bearer {access_token}"}
    r_info = requests.get(f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*", headers=info_headers)
    if r_info.status_code == 200 and len(r_info.json()) > 0:
        data = r_info.json()[0]
        print(f"✅ 当前状态: {data.get('name')} | 过期时间: {data.get('expire_time')}")
    else:
        print("⚠️ 无法获取过期时间，请登录网页确认。")

if __name__ == "__main__":
    run_task()
