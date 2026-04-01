import requests
import os
import time

# ================= 核心配置 (已从你提供的代码中提取) =================
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"
SERVER_ID = "1ed88a77-8513-43f9-9d1e-3a0db85b84b5"

# 账号信息 (通过 GitHub Secrets 获取)
EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
# =================================================================

def run_task():
    if not EMAIL or not PASSWORD:
        print("❌ 错误: 请在 GitHub Secrets 中设置 FXC_EMAIL 和 FXC_PASS")
        return

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
        "X-Client-Info": "supabase-ssr/0.8.0"
    }

    print(f"📡 正在尝试登录账号: {EMAIL}...")
    
    # 1. 登录
    login_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
    try:
        res = requests.post(login_url, json={"email": EMAIL, "password": PASSWORD}, headers=headers)
        if res.status_code != 200:
            print(f"❌ 登录失败: {res.text}")
            return
        
        access_token = res.json().get("access_token")
        headers["Authorization"] = f"Bearer {access_token}"
        print("✅ 登录成功！")

        # 2. 调用续期 RPC
        # 根据 FreeXCraft 的前端逻辑，函数名通常为 renew_server
        renew_url = f"{SUPABASE_URL}/rest/v1/rpc/renew_server"
        print(f"🛠️ 正在为服务器 {SERVER_ID} 发送续期请求...")
        
        renew_res = requests.post(renew_url, json={"server_id": SERVER_ID}, headers=headers)
        
        if renew_res.status_code in [200, 201, 204]:
            print("🎉 续期成功！服务器已重置过期时间。")
        elif "captcha" in renew_res.text.lower():
            print("🛑 续期失败：该接口已强制开启验证码校验。此 API 脚本已失效。")
        else:
            print(f"⚠️ 续期请求反馈 ({renew_res.status_code}): {renew_res.text}")

        # 3. 查询当前剩余时间
        info_url = f"{SUPABASE_URL}/rest/v1/servers?id=eq.{SERVER_ID}&select=*"
        time.sleep(1) # 稍等数据库更新
        info_res = requests.get(info_url, headers=headers)
        if info_res.status_code == 200:
            data = info_res.json()[0]
            print(f"📊 当前状态: {data.get('name')} | 过期时间: {data.get('expire_time')}")

    except Exception as e:
        print(f"❗ 脚本运行出错: {e}")

if __name__ == "__main__":
    run_task()
