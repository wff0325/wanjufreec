#!/usr/bin/env python3
"""
FreeXCraft 服务器自动续期脚本
每小时自动访问续期页面并点击续期按钮
"""

import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('renewal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置信息
URL = "https://freexcraft.com/external-renew"
SUBDOMAIN = "laohu.xmania.me"
TIMEOUT = 30000  # 30秒超时


async def renew_server():
    """执行服务器续期操作"""
    logger.info("="*60)
    logger.info(f"开始执行服务器续期 - {datetime.now()}")
    logger.info("="*60)
    
    try:
        async with async_playwright() as p:
            # 启动浏览器（无头模式）
            logger.info("正在启动浏览器...")
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 创建新页面
            page = await browser.new_page()
            
            # 设置超时时间
            page.set_default_timeout(TIMEOUT)
            
            # 访问续期页面
            logger.info(f"正在访问 {URL}")
            await page.goto(URL, wait_until="domcontentloaded")
            logger.info("页面 DOM 加载完成")
            
            # 等待更长时间让页面完全加载
            await page.wait_for_timeout(3000)
            
            # 截图查看页面状态
            await page.screenshot(path='page_loaded.png')
            logger.info("已保存页面截图: page_loaded.png")
            
            # 打印页面 HTML 用于调试
            content = await page.content()
            logger.debug(f"页面内容长度: {len(content)} 字符")
            
            # 尝试多种选择器找到输入框
            logger.info("正在查找输入框...")
            input_selectors = [
                'input[type="text"]',
                'input.input',
                'input[placeholder*="subdomain"]',
                'input[placeholder*="myserver"]',
                'input',
                '#subdomain',
                '[name="subdomain"]',
            ]
            
            input_field = None
            for selector in input_selectors:
                try:
                    input_field = await page.query_selector(selector)
                    if input_field:
                        # 检查是否可见
                        is_visible = await input_field.is_visible()
                        if is_visible:
                            logger.info(f"找到输入框（选择器: {selector}）")
                            break
                        else:
                            logger.debug(f"找到输入框但不可见（选择器: {selector}）")
                            input_field = None
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
            
            if not input_field:
                logger.error("找不到输入框！保存页面 HTML 用于调试")
                with open('page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                raise Exception("未找到输入框元素")
            
            # 填写子域名
            logger.info(f"正在填写子域名: {SUBDOMAIN}")
            await input_field.fill(SUBDOMAIN)
            logger.info("子域名填写完成")
            
            # 等待一下让页面处理
            await page.wait_for_timeout(2000)
            
            # 截图查看填写后的状态
            await page.screenshot(path='after_fill.png')
            logger.info("已保存填写后截图: after_fill.png")
            
            # 点击 "Renew & Start" 按钮
            logger.info("正在查找 Renew & Start 按钮...")
            
            # 尝试多种选择器来找到按钮
            button_clicked = False
            button_selectors = [
                'button:has-text("Renew & Start")',
                'button:has-text("Renew")',
                'button:has-text("Start")',
                'button[type="submit"]',
                'button.btn',
                '.btn:has-text("Renew")',
                'button',
            ]
            
            for selector in button_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    for button in buttons:
                        text = await button.text_content()
                        is_visible = await button.is_visible()
                        logger.debug(f"找到按钮: '{text}' (可见: {is_visible}, 选择器: {selector})")
                        
                        if is_visible and text and ('renew' in text.lower() or 'start' in text.lower()):
                            logger.info(f"准备点击按钮: '{text}'")
                            await button.click()
                            button_clicked = True
                            logger.info(f"成功点击按钮")
                            break
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
                
                if button_clicked:
                    break
            
            if not button_clicked:
                logger.warning("使用常规选择器未找到按钮，尝试 JavaScript 点击...")
                try:
                    # 使用 JavaScript 查找并点击按钮
                    await page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button');
                            for (const button of buttons) {
                                if (button.textContent.includes('Renew') || button.textContent.includes('Start')) {
                                    button.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    button_clicked = True
                    logger.info("已使用 JavaScript 点击按钮")
                except Exception as e:
                    logger.error(f"JavaScript 点击失败: {e}")
            
            # 等待响应
            logger.info("等待页面响应...")
            await page.wait_for_timeout(5000)
            
            # 截图查看最终结果
            await page.screenshot(path='final_result.png')
            logger.info("已保存最终结果截图: final_result.png")
            
            # 检查页面响应
            page_content = await page.content()
            page_text = await page.evaluate("() => document.body.innerText")
            
            logger.info(f"页面文本内容: {page_text[:500]}")  # 打印前500字符
            
            # 检查是否在冷却期
            cooldown_messages = [
                "cooldown",
                "try again in",
                "wait"
            ]
            
            is_cooldown = any(msg.lower() in page_text.lower() for msg in cooldown_messages)
            
            if is_cooldown:
                logger.info("⏰ 续期在冷却期中（1小时内已经续期过）")
                logger.info("这是正常的！服务器已经在运行中，无需担心")
                return True  # 这也算是成功的情况
            
            # 检查是否有成功消息
            success_messages = [
                "Server renewed",
                "already running",
                "renewed, but the server is already running",
                "extended",
                "started",
                "renewed successfully"
            ]
            
            success = any(msg.lower() in page_content.lower() or msg.lower() in page_text.lower() 
                         for msg in success_messages)
            
            if success:
                logger.info("✓ 续期成功！服务器已续期并启动")
            else:
                logger.warning(f"无法确认续期状态，页面可能已变化")
                logger.warning(f"请检查截图文件: final_result.png")
            
            # 关闭浏览器
            await browser.close()
            logger.info("浏览器已关闭")
            
            return success
            
    except Exception as e:
        logger.error(f"续期过程出错: {str(e)}", exc_info=True)
        return False


async def main():
    """主函数"""
    try:
        success = await renew_server()
        
        if success:
            logger.info("="*60)
            logger.info("续期任务完成 ✓")
            logger.info("="*60)
        else:
            logger.warning("="*60)
            logger.warning("续期任务完成，但状态未确认")
            logger.warning("="*60)
            
    except Exception as e:
        logger.error(f"主程序错误: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
