import requests
import os
import json
import base64
import re
import time

# ================= 调试配置 =================
SERVER_ID = "c2c11e40-1821-47c2-bd50-5651cdcbf268"
SUPABASE_URL = "https://aeilbxxjgrnnqmtwnesh.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFlaWxieHhqZ3JubnFtdHduZXNoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzEzMTY4NjUsImV4cCI6MjA4Njg5Mjg2NX0.ZuGQzVsHX8nnvo1JFoBCOokEjaW-no-QKEe_yco7kUA"

EMAIL = os.getenv("FXC_EMAIL")
PASSWORD = os.getenv("FXC_PASS")
# ===========================================

def debug_scan():
    if not EMAIL or not PASSWORD:
        print("❌ 错误: 请先设置环境变量 FXC_EMAIL 和 FXC_PASS")
        return

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    })

    # 1. 登录以获取访问权限
    print("📡 1. 正在登录 Supabase 获取授权...")
    login_headers = {"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}
    r_login = session.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password", 
                          json={"email": EMAIL, "password": PASSWORD}, headers=login_headers)
    
    if r_login.status_code != 200:
        print(f"❌ 登录失败: {r_login.text}")
        return
    
    auth_data = r_login.json()
    print("✅ 登录成功！")

    # 2. 注入网页所需的加密 Cookie (否则会被重定向到登录页)
    cookie_dict = {
        "access_token": auth_data.get("access_token"),
        "refresh_token": auth_data.get("refresh_token"),
        "token_type": "bearer",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "user": auth_data.get("user")
    }
    cookie_val = f"base64-{base64.b64encode(json.dumps(cookie_dict).encode()).decode()}"
    session.cookies.set("sb-aeilbxxjgrnnqmtwnesh-auth-token", cookie_val, domain="freexcraft.com")

    # 3. 抓取控制面板源码
    print(f"🌐 2. 正在访问服务器面板: https://freexcraft.com/dashboard/server/{SERVER_ID}")
    dashboard_url = f"https://freexcraft.com/dashboard/server/{SERVER_ID}"
    r_page = session.get(dashboard_url)
    
    if r_page.status_code != 200:
        print(f"❌ 访问页面失败，状态码: {r_page.status_code}")
        return

    html = r_page.text
    print(f"📄 页面源码长度: {len(html)} 字符")

    # 4. 深度扫描 Action ID (Next.js 的特征是 40 位十六进制字符串)
    print("\n🔍 3. 开始全量扫描 40 位 Action ID 哈希...")
    
    # 正则匹配 40 位 [a-f0-9]
    found_ids = re.findall(r'[a-f0-9]{40}', html)
    
    # 去重
    unique_ids = list(set(found_ids))
    
    if not unique_ids:
        print("❓ 未在主 HTML 中找到任何 40 位哈希。可能 ID 被藏在外部 JS 文件里了。")
        # 尝试寻找 JS 引用
        js_files = re.findall(r'/_next/static/chunks/[a-zA-Z0-9-]+\.js', html)
        print(f"🔎 发现 {len(js_files)} 个外部 JS 文件，可能需要进一步爬取。")
    else:
        print(f"🎯 扫描完成！共发现 {len(unique_ids)} 个可能的 Action ID：")
        print("-" * 60)
        for i, aid in enumerate(unique_ids):
            # 标记出我们已知的那个 ID
            mark = " [当前正使用的 ID!]" if aid == "40f53a98e53e936c81bbae1afe242f83ecba099143" else ""
            
            # 寻找该 ID 附近的上下文，判断它的用途
            pos = html.find(aid)
            context = html[max(0, pos-40) : min(len(html), pos+80)].replace('\n', ' ')
            
            print(f"[{i+1}] {aid}{mark}")
            print(f"    上下文: ...{context}...")
            print("-" * 60)

    # 5. 检查是否含有 "EXTEND TIME" 关键词
    if "EXTEND TIME" in html:
        print("\n✅ 确认页面包含 'EXTEND TIME' 按钮文本。")
    else:
        print("\n❌ 警告：页面源码中没看到 'EXTEND TIME' 文本，可能页面渲染方式改变。")

if __name__ == "__main__":
    debug_scan()
