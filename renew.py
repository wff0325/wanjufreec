import requests
import os
import time

# ================= 核心配置 =================
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"
SERVER_ID = "1ed88a77-8513-43f9-9d1e-3a0db85b84b5"

EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
# ==========================================

def run_task():
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
        "X-Client-Info": "supabase-ssr/0.8.0"
    }

    print(f"📡 正在登录: {EMAIL}...")
    login_res = requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                             json={"email": EMAIL, "password": PASSWORD}, headers=headers)
    
    if login_res.status_code != 200:
        print("❌ 登录失败")
        return
    
    token = login_res.json().get("access_token")
    headers["Authorization"] = f"Bearer {token}"
    print("✅ 登录成功")

    # --- 尝试不同的函数名和参数组合 ---
    # 组合 1: 常见组合 (函数: renew_server, 参数: id)
    # 组合 2: 你之前试过的 (函数: renew_server, 参数: server_id)
    # 组合 3: 备选组合 (函数: extend_server, 参数: id)
    
    attempts = [
        ("renew_server", {"id": SERVER_ID}),
        ("renew_server", {"server_id": SERVER_ID}),
        ("extend_server", {"id": SERVER_ID}),
        ("renew", {"id": SERVER_ID})
    ]

    success = False
    for func_name, payload in attempts:
        print(f"🛠️ 尝试调用: {func_name} | 参数: {list(payload.keys())[0]}...")
        url = f"{SUPABASE_URL}/rest/v1/rpc/{func_name}"
        res = requests.post(url, json=payload, headers=headers)
        
        if res.status_code in [200, 201, 204]:
            print(f"🎉 成功！使用的函数是: {func_name}")
            success = True
            break
        else:
            print(f"  ❌ 失败 (状态码 {res.status_code})")

    if not success:
        print("\n🆘 所有已知组合都失败了。")
        print("请手动点一下网页上的 EXTEND TIME，然后在 F12 的 Network(网络) 里找红色以外的请求，看它的 'Payload(负载)' 里的参数名到底叫什么。")

    # 最后查询一次状态
    info_res = requests.get(f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*", headers=headers)
    if info_res.status_code == 200:
        data = info_res.json()[0]
        print(f"\n📊 当前服务器: {data.get('name')} | 过期时间: {data.get('expire_time')}")

if __name__ == "__main__":
    run_task()
