import os
import sys
import json
import asyncio

# 1. التحقق من وجود مكتبة Camoufox
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل بيئة التخفي بنجاح.")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox. يرجى تثبيتها عبر: pip install camoufox")
    sys.exit(1)

# الإعدادات الخاصة بـ ChatGPT
CHATGPT_URL = "https://chatgpt.com"

async def run_chatgpt_automation(prompt):
    print(f"🧐 جاري معالجة طلبك: {prompt}")
    
    output = {"status": "error", "message": "فشل غير معروف"}

    try:
        # 2. تشغيل المتصفح
        async with AsyncCamoufox(
            headless=True,             
            block_images=True,         
            i_know_what_im_doing=True, 
            humanize=True,             
        ) as browser:
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # الكوكيز
            cookies_json = os.getenv("CHATGPT_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                except: pass

            page = await context.new_page()
            
            print("🌐 الدخول إلى ChatGPT...")
            await page.goto(CHATGPT_URL, wait_until="networkidle", timeout=60000)

            input_selector = "#prompt-textarea"
            try:
                await page.wait_for_selector(input_selector, timeout=30000)
            except:
                print("❌ فشل العثور على المدخل.")
                return

            print("✍️ إرسال السؤال...")
            await page.fill(input_selector, prompt)
            await asyncio.sleep(1) 
            await page.keyboard.press("Enter")
            
            response_selector = ".markdown.prose"
            stop_button_selector = 'button[data-testid="stop-button"], button[aria-label="Stop generating"]'
            
            print("📡 بانتظار الاستجابة...")
            await page.wait_for_selector(response_selector, timeout=60000)
            
            max_wait = 90  
            for i in range(max_wait):
                is_writing = await page.query_selector(stop_button_selector)
                if not is_writing and i > 2: 
                    break
                await asyncio.sleep(1)

            # 9. استخراج الرد مع التنظيف الذكي (Smart Cleaning)
            final_res_html = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll("{response_selector}");
                if (els.length === 0) return "خطأ في جلب المحتوى.";
                
                const lastMsg = els[els.length - 1].cloneNode(true);

                // أ. حذف الأزرار والأيقونات فوراً
                lastMsg.querySelectorAll('button, svg, .sr-only').forEach(el => el.remove());

                // ب. تنظيف صناديق الكود بدقة
                const preBlocks = lastMsg.querySelectorAll('pre');
                preBlocks.forEach(pre => {{
                    // 1. حذف أي شريط علوي (Header) يحتوي على "Copy code" أو اسم اللغة
                    // نبحث عن أي Div في بداية الـ pre يحتوي على نصوص تحكم
                    const possibleHeaders = pre.querySelectorAll('div');
                    possibleHeaders.forEach(div => {{
                        if (div.innerText.toLowerCase().includes('copy') || 
                            div.innerText.toLowerCase().includes('python') ||
                            div.classList.contains('flex')) {{
                            div.remove();
                        }}
                    }});

                    // 2. معالجة نص الكود داخل وسم code
                    const codeTag = pre.querySelector('code');
                    if (codeTag) {{
                        let rawText = codeTag.innerText;
                        let lines = rawText.split('\\n');

                        // التحقق: إذا كان السطر الأول هو مجرد اسم لغة برمجة (بدون أكواد)، نحذفه
                        const commonLangs = ['python', 'javascript', 'html', 'css', 'sql', 'bash', 'json'];
                        if (lines.length > 0) {{
                            const firstLine = lines[0].trim().toLowerCase();
                            if (commonLangs.includes(firstLine) || firstLine === "code") {{
                                lines.shift();
                            }}
                        }

                        // إعادة بناء الكود وتنظيف الفراغات في البداية والنهاية
                        codeTag.innerText = lines.join('\\n').trim();
                    }}
                }});

                return lastMsg.innerHTML; 
            }}''')

            output = {"status": "success", "response": final_res_html}

    except Exception as e:
        output = {"status": "error", "message": str(e)}

    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("✅ تمت العملية بنجاح.")

if __name__ == "__main__":
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "مرحباً"
    asyncio.run(run_chatgpt_automation(user_prompt))
