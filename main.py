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
    
    # القيمة الافتراضية للمخرجات
    output = {"status": "error", "message": "فشل غير معروف"}

    try:
        # 2. تشغيل المتصفح مع تفعيل خصائص محاكاة البشر
        async with AsyncCamoufox(
            headless=True,             
            block_images=True,         
            i_know_what_im_doing=True, 
            humanize=True,             
        ) as browser:
            
            # 3. إعداد السياق (Context)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # 4. التعامل مع الكوكيز (Session)
            cookies_json = os.getenv("CHATGPT_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم استيراد الجلسة من الكوكيز.")
                except Exception as e:
                    print(f"⚠️ تحذير: فشل استيراد الكوكيز: {e}")

            page = await context.new_page()
            
            # 5. التوجه للموقع
            print("🌐 الدخول إلى ChatGPT...")
            await page.goto(CHATGPT_URL, wait_until="networkidle", timeout=60000)

            # 6. تحديد صندوق الكتابة
            input_selector = "#prompt-textarea"
            try:
                await page.wait_for_selector(input_selector, timeout=30000)
            except:
                print("❌ لم نجد صندوق الكتابة. قد يكون الموقع يطلب تسجيل دخول أو اختبار Bot.")
                return

            # 7. إرسال السؤال
            print("✍️ كتابة السؤال...")
            await page.fill(input_selector, prompt)
            await asyncio.sleep(1) 
            await page.keyboard.press("Enter")
            
            # 8. مراقبة الرد
            response_selector = ".markdown.prose"
            stop_button_selector = 'button[data-testid="stop-button"], button[aria-label="Stop generating"]'
            
            print("📡 بانتظار استجابة الذكاء الاصطناعي...")
            await page.wait_for_selector(response_selector, timeout=60000)
            
            # الانتظار حتى اكتمال الكتابة
            max_wait = 90  
            for i in range(max_wait):
                is_writing = await page.query_selector(stop_button_selector)
                if not is_writing and i > 2: 
                    break
                await asyncio.sleep(1)

            # 9. استخراج الرد الأخير مع "التنظيف العميق"
            # نقوم بحذف الأزرار، الأيقونات، وأول سطر من كل صندوق برمجبي (اسم اللغة)
            final_res_html = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll("{response_selector}");
                if (els.length === 0) return "خطأ: تعذر العثور على محتوى الرد.";
                
                // نأخذ نسخة من الرسالة الأخيرة للعمل عليها
                const lastMsg = els[els.length - 1].cloneNode(true);

                // أ. حذف جميع الأزرار (أزرار النسخ، الاستماع، إلخ)
                const buttons = lastMsg.querySelectorAll('button');
                buttons.forEach(btn => btn.remove());

                // ب. حذف الأيقونات (SVG) التي قد تظهر بجانب العناوين أو الأزرار
                const svgs = lastMsg.querySelectorAll('svg');
                svgs.forEach(svg => svg.remove());

                // ج. معالجة صناديق الكود: حذف أول سطر (الذي يحتوي عادةً على اسم اللغة أو Copy code)
                const preBlocks = lastMsg.querySelectorAll('pre');
                preBlocks.forEach(pre => {{
                    const code = pre.querySelector('code');
                    if (code) {{
                        let content = code.innerText;
                        let lines = content.split('\\n');
                        if (lines.length > 1) {{
                            lines.shift(); // حذف السطر الأول دائماً
                            code.innerText = lines.join('\\n');
                        }}
                    }}
                }});

                return lastMsg.innerHTML; 
            }}''')

            output = {"status": "success", "response": final_res_html}

    except Exception as e:
        print(f"❌ حدث خطأ تقني: {e}")
        output = {"status": "error", "message": str(e)}

    # 10. حفظ النتيجة
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("✅ تمت العملية بنجاح. النتيجة في result.json")

if __name__ == "__main__":
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "مرحباً، كيف حالك؟"
    asyncio.run(run_chatgpt_automation(user_prompt))
