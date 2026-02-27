import os
import sys
import json
import asyncio

# 1. التحقق من البيئة والمحرك
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل بيئة ChatGPT المتطورة.")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox. تأكد من تثبيتها عبر pip install camoufox.")
    sys.exit(1)

# الإعدادات الأساسية
CHATGPT_URL = "https://chatgpt.com"
# المحددات الخاصة بـ ChatGPT (Selectors)
INPUT_SELECTOR = "#prompt-textarea"
# نختار حاوية الرد الخاصة بالمساعد والتي تحتوي على التنسيق
RESPONSE_SELECTOR = 'div[data-message-author-role="assistant"] .markdown'

async def run_chatgpt_automation(prompt):
    print(f"🧐 جاري معالجة الطلب: {prompt}")
    
    # هيكل افتراضي للمخرجات
    output = {"status": "error", "message": "فشل التشغيل المبدئي"}

    try:
        # 2. إعداد المتصفح بتقنيات تخفي متقدمة
        async with AsyncCamoufox(
            headless=True,            # غيرها لـ False إذا أردت رؤية ما يحدث يدوياً
            block_images=True,        
            i_know_what_im_doing=True, 
            humanize=True,            
        ) as browser:
            
            # 3. إعداد سياق المتصفح
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # 4. إدارة الجلسة عبر الكوكيز (تم تصحيح منطق الشرط هنا)
            cookies_json = os.getenv("CHATGPT_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم حقن كوكيز الجلسة بنجاح.")
                except Exception as e:
                    print(f"⚠️ خطأ في معالجة الكوكيز (تنسيق JSON غير صحيح): {e}")
            else:
                print("⚠️ تحذير: لم يتم العثور على متغير CHATGPT_COOKIES.")

            page = await context.new_page()
            
            # 5. الدخول إلى الموقع مع آلية إعادة المحاولة (Retry Logic)
            print("🌐 الإبحار إلى ChatGPT...")
            success_loading = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    # ننتظر حتى تصبح الشبكة هادئة لضمان تحميل واجهة React
                    await page.goto(CHATGPT_URL, wait_until="networkidle", timeout=60000)
                    await page.wait_for_selector(INPUT_SELECTOR, timeout=25000)
                    success_loading = True
                    print(f"✅ تم تحميل واجهة الدردشة بنجاح في المحاولة رقم {attempt + 1}.")
                    break
                except Exception as e:
                    print(f"🔄 محاولة {attempt + 1} لم تنجح في العثور على صندوق الإدخال...")
                    if attempt == max_retries - 1:
                        await page.screenshot(path="error_debug.png")
                        print("📸 تم حفظ صورة للخطأ في error_debug.png")
                    else:
                        await asyncio.sleep(2)

            if not success_loading:
                raise Exception("تعذر الوصول لـ ChatGPT (ربما Cloudflare أو الحاجة لتسجيل الدخول).")

            # 6. كتابة السؤال وإرساله
            print("✍️ كتابة السؤال وإرساله...")
            await page.fill(INPUT_SELECTOR, prompt)
            await asyncio.sleep(1) # تأخير بسيط لمحاكاة التفاعل البشري
            await page.keyboard.press("Enter")
            
            # 7. مراقبة تدفق الرد واستقراره
            print("📡 بانتظار رد الذكاء الاصطناعي...")
            # ننتظر ظهور أول رد من المساعد
            await page.wait_for_selector(RESPONSE_SELECTOR, timeout=60000)
            
            previous_html = ""
            stable_count = 0
            
            # فحص استقرار الرد
            for _ in range(120): 
                current_html = await page.evaluate(f'''() => {{
                    const els = document.querySelectorAll('{RESPONSE_SELECTOR}');
                    return els.length > 0 ? els[els.length - 1].innerHTML : "";
                }}''')
                
                if len(current_html) > len(previous_html):
                    previous_html = current_html
                    stable_count = 0
                elif len(current_html) > 0:
                    # إذا لم يتغير الطول، نزيد عداد الاستقرار
                    stable_count += 1
                
                # إذا استقر الرد لـ 6 دورات (تقريباً 6 ثوانٍ)، نعتبره اكتمل
                if stable_count >= 6:
                    print(f"✅ تم التقاط الرد المنسق بالكامل.")
                    break
                
                await asyncio.sleep(1)

            # 8. استخراج النتيجة النهائية
            final_res_html = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll('{RESPONSE_SELECTOR}');
                if (els.length > 0) {{
                    return els[els.length - 1].innerHTML; 
                }}
                return "خطأ: لم نتمكن من العثور على محتوى الرد.";
            }}''')

            output = {"status": "success", "response": final_res_html}

    except Exception as e:
        print(f"❌ حدث خطأ غير متوقع: {e}")
        output = {"status": "error", "message": str(e)}

    # 9. حفظ النتيجة النهائية بتنسيق UTF-8
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم حفظ الرد في result.json")

if __name__ == "__main__":
    # قراءة السؤال من سطر الأوامر
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "اكتب ٢ كود بايثون و ٢ كود js مع شرح كل منهم وجدول مقارنة بين اللغتين"
    asyncio.run(run_chatgpt_automation(user_prompt))
