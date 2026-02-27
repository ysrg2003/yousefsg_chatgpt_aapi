import os
import sys
import json
import asyncio

# 1. التحقق من البيئة والمحرك
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 المحرك جاهز: تم تفعيل بيئة ChatGPT بنجاح.")
except ImportError:
    print("❌ خطأ: لم يتم العثور على مكتبة Camoufox.")
    sys.exit(1)

# الرابط الأساسي لـ ChatGPT
CHATGPT_URL = "https://chatgpt.com/"

async def run_chatgpt_automation(prompt):
    print(f"🧐 جاري معالجة السؤال: {prompt}")
    
    output = {"status": "error", "message": "فشل التشغيل المبدئي"}

    try:
        # 2. إعداد المتصفح بتقنيات التخفي
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

            # 3. إدارة الجلسة عبر الكوكيز (مهم جداً لـ ChatGPT)
            cookies_json = os.getenv("CHATGPT_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم حقن كوكيز الجلسة.")
                except Exception as e:
                    print(f"⚠️ خطأ في الكوكيز: {e}")

            page = await context.new_page()
            
            # 4. الدخول إلى الموقع
            print("🌐 الإبحار إلى ChatGPT...")
            await page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=60000)

            # 5. البحث عن صندوق الإدخال (Selector الخاص بـ ChatGPT)
            # ChatGPT يستخدم غالباً textarea بمعرف #prompt-textarea
            input_selector = "#prompt-textarea"
            try:
                await page.wait_for_selector(input_selector, timeout=30000)
            except:
                print("❌ تعذر العثور على مربع النص. قد تحتاج لتحديث الكوكيز أو تجاوز التحقق (Cloudflare).")
                return

            # 6. كتابة السؤال وإرساله
            print("✍️ كتابة السؤال...")
            await page.fill(input_selector, prompt)
            await page.keyboard.press("Enter")
            
            # 7. مراقبة الرد (Streaming)
            print("📡 بانتظار رد ChatGPT...")
            # ChatGPT يضع الردود داخل divs بتنسيق markdown (فئة .prose)
            response_selector = ".prose"
            
            await page.wait_for_selector(response_selector, timeout=60000)
            
            previous_html = ""
            stable_count = 0
            
            # فحص استقرار الرد
            for attempt in range(120): # ChatGPT قد يكون أبطأ قليلاً في الردود الطويلة
                current_html = await page.evaluate(f'''() => {{
                    const els = document.querySelectorAll("{response_selector}");
                    return els.length > 0 ? els[els.length - 1].innerHTML : "";
                }}''')
                
                if len(current_html) > len(previous_html):
                    previous_html = current_html
                    stable_count = 0
                elif len(current_html) > 0:
                    stable_count += 1
                
                # إذا لم يتغير النص لمدة 5 ثوانٍ، نعتبره انتهى
                if stable_count >= 5:
                    print(f"✅ تم اكتمال الرد.")
                    break
                
                await asyncio.sleep(1)

            # 8. استخراج النتيجة النهائية
            final_res_html = await page.evaluate(f'''() => {{
                const els = document.querySelectorAll("{response_selector}");
                return els.length > 0 ? els[els.length - 1].innerHTML : "خطأ في استخراج المحتوى";
            }}''')

            output = {"status": "success", "response": final_res_html}

    except Exception as e:
        print(f"❌ حدث خطأ: {e}")
        output = {"status": "error", "message": str(e)}

    # 9. حفظ النتيجة
    with open("chatgpt_result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم حفظ الرد في chatgpt_result.json")

if __name__ == "__main__":
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else "أهلاً، كيف حالك اليوم؟"
    asyncio.run(run_chatgpt_automation(user_prompt))
