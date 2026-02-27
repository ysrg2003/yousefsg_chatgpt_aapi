import os
import sys
import json
import asyncio

# 1. التحقق من البيئة والمحرك
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل بيئة ChatGPT بنجاح.")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox. تأكد من توفرها في مسار PYTHONPATH.")
    sys.exit(1)

# الرابط الأساسي لـ ChatGPT
CHATGPT_URL = "https://chatgpt.com"

async def run_gpt_automation(prompt):
    print(f"🧐 جاري معالجة الطلب لـ ChatGPT: {prompt}")
    
    # هيكل افتراضي للمخرجات في حال حدث خطأ
    output = {"status": "error", "message": "فشل التشغيل المبدئي"}

    try:
        # 2. إعداد المتصفح بتقنيات التخفي (Anti-Bot)
        # تم الحفاظ على إعدادات التخفي المتقدمة لتجاوز Cloudflare
        async with AsyncCamoufox(
            headless=True,            
            block_images=True,        
            i_know_what_im_doing=True, 
            humanize=True,            
        ) as browser:
            
            # 3. إعداد سياق المتصفح (Context)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # 4. إدارة الجلسة عبر كوكيز ChatGPT
            # يتم جلب الكوكيز من سكرت GPT_COOKIES بدلاً من GEMINI_COOKIES
            cookies_json = os.getenv("GPT_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم حقن كوكيز جلسة ChatGPT بنجاح.")
                except Exception as e:
                    print(f"⚠️ خطأ في الكوكيز: {e}")

            page = await context.new_page()
            
            # 5. الدخول إلى الموقع
            print("🌐 الإبحار إلى ChatGPT...")
            await page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=60000)

            # 6. البحث عن صندوق الإدخال الخاص بـ ChatGPT
            # المعرف الافتراضي في ChatGPT هو #prompt-textarea
            input_selector = "#prompt-textarea"
            await page.wait_for_selector(input_selector, timeout=30000)
            
            # 7. كتابة السؤال وإرساله
            print("✍️ كتابة السؤال وإرساله...")
            await page.fill(input_selector, prompt)
            await asyncio.sleep(1) # تأخير بسيط للمحاكاة البشرية
            await page.keyboard.press("Enter")
            
            # 8. مراقبة "تدفق" الرد (Streaming Response)
            print("📡 بانتظار رد الذكاء الاصطناعي...")
            # ردود ChatGPT تكون عادةً داخل عنصر markdown
            response_selector = ".markdown.prose, .agent-turn .markdown"
            
            # ننتظر أول ظهور للرد
            await page.wait_for_selector(response_selector, timeout=60000)
            
            previous_html = ""
            stable_count = 0
            
            # فحص استقرار الرد لضمان اكتمال النص المنسق
            for attempt in range(90): 
                current_html = await page.evaluate(f'''() => {{
                    const els = document.querySelectorAll("{response_selector}");
                    return els.length > 0 ? els[els.length - 1].innerHTML : "";
                }}''')
                
                # إذا زاد طول الـ HTML، يعني أن الرد لا يزال يُكتب
                if len(current_html) > len(previous_html):
                    previous_html = current_html
                    stable_count = 0
                elif len(current_html) > 0:
                    stable_count += 1
                
                # إذا استقر الرد لـ 8 ثوانٍ، نعتبره اكتمل
                if stable_count >= 8:
                    print(f"✅ تم التقاط الرد المنسق بالكامل.")
                    break
                
                await asyncio.sleep(1)

            # 9. استخراج النتيجة النهائية بـ HTML
            final_res_html = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll("{response_selector}");
                if (els.length > 0) {{
                    return els[els.length - 1].innerHTML; 
                }}
                return "خطأ: لم نتمكن من العثور على محتوى الرد.";
            }}''')

            output = {"status": "success", "response": final_res_html}

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")
        output = {"status": "error", "message": str(e)}

    # 10. حفظ النتيجة النهائية بتنسيق UTF-8
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم حفظ الرد في result.json")

if __name__ == "__main__":
    # قراءة السؤال من سطر الأوامر
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(run_gpt_automation(user_prompt))
