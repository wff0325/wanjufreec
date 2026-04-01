import requests
import os
import json
import base64
import time

# --- 配置 (已验证) ---
SERVER_ID = "1ed88a77-8513-43f9-9d1e-3a0db85b84b5"
ACTION_ID = "40f34f412fbff5791ab05264298fe5d6879efba201" 
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"

EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")

def find_the_data():
    session = requests.Session()
    login_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    
    # 1. 登录
    print("📡 正在获取授权...")
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json={"email": EMAIL, "password": PASSWORD}, headers=login_headers)
    
    if r_login.status_code != 200:
        print("❌ 登录失败")
        return
    
    token = r_login.json().get("access_token")
    print("✅ 授权成功")

    # 2. 发送续期 (Action)
    print("🛠️ 执行续期...")
    action_headers = {"next-action": ACTION_ID, "referer": f"https://freexcraft.com/dashboard/server/{SERVER_ID}"}
    session.post(f"https://freexcraft.com/dashboard/server/{SERVER_ID}", data=f'["{SERVER_ID}"]', headers=action_headers)

    # 3. 核心步骤：深挖数据库字段
    print("\n🔍 --- 正在解析服务器原始数据包 ---")
    info_headers = {
        "apikey": SUPABASE_ANON_KEY, 
        "Authorization": f"Bearer {token}",
        "Range": "0-9"
    }
    # 获取 servers 表中该 ID 的所有数据
    r_info = requests.get(f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*", headers=info_headers)
    
    if r_info.status_code == 200 and len(r_info.json()) > 0:
        raw_data = r_info.json()[0]
        print(f"数据获取成功！当前服务器共有 {len(raw_data)} 个字段：")
        print("-" * 50)
        # 打印所有非空的字段
        for key, value in raw_data.items():
            # 标记出可能是时间的字段
            mark = " <--- 🚩 可能是这个！" if any(x in key.lower() for x in ['at', 'time', 'date', 'reset']) else ""
            print(f"字段名: [{key:20}] | 值: {value}{mark}")
        print("-" * 50)
        print("\n💡 请对照网页上的倒计时，看哪个时间戳是刚刚更新的（现在的时刻）。")
    else:
        print(f"❌ 无法读取数据，错误: {r_info.text}")

if __name__ == "__main__":
    find_the_data()
