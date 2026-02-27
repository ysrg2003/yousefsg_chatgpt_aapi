import os
import sys
import json
import asyncio

# التحقق من وجود المحرك
try:
    from camoufox.async_api import AsyncCamoufox
    print("🚀 محرك ChatGPT الذكي جاهز للعمل.")
except ImportError:
    print("❌ خطأ: مكتبة Camoufox غير متوفرة.")
    sys.exit(1)

CHATGPT_URL = "https://chatgpt.com"

async def run_gpt_automation(prompt):
    print(f"🧐 الطلب المستلم: {prompt}")
    output = {"status": "error", "message": "حدث خطأ غير متوقع"}

    try:
        # إعداد المتصفح بأقصى درجات التخفي والسرعة
        async with AsyncCamoufox(
            headless=True,
            block_images=True, # توفير الوقت والبيانات
            i_know_what_im_doing=True,
            humanize=True,
        ) as browser:
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            )

            # حقن الكوكيز لضمان تسجيل الدخول وتخطي Cloudflare
            cookies_json = os.getenv("GPT_COOKIES")
            if cookies_json:
                try:
                    await context.add_cookies(json.loads(cookies_json))
                    print("🔑 تم استعادة الجلسة بنجاح.")
                except:
                    print("⚠️ فشل في حقن الكوكيز، سيتم المحاولة كزائر.")

            page = await context.new_page()
            
            # التحسين 1: استخدام networkidle لضمان تحميل سكريبتات ChatGPT المعقدة
            print("🌐 الإبحار إلى ChatGPT...")
            await page.goto(CHATGPT_URL, wait_until="networkidle", timeout=90000)

            # التحسين 2: البحث عن أي عنصر إدخال متاح (مرونة عالية)
            input_selector = "#prompt-textarea, [contenteditable='true'], textarea"
            try:
                await page.wait_for_selector(input_selector, timeout=30000)
            except:
                # محاولة أخيرة بالضغط على المفتاح Tab للوصول للصندوق إذا تغير الـ ID
                await page.keyboard.press("Tab")
            
            print("✍️ إرسال البيانات...")
            await page.fill(input_selector, prompt)
            await asyncio.sleep(0.5)
            await page.keyboard.press("Enter")
            
            print("📡 بانتظار استجابة النظام (فحص ديناميكي)...")
            
            # التحسين 3: "الحل الجذري" - مراقبة الـ DOM داخلياً عبر JavaScript
            # ننتظر حتى يبدأ الرد، ثم ننتظر حتى يختفي مؤشر "جاري الكتابة"
            
            final_html = ""
            max_wait = 150 # زيادة الوقت للطلبات الطويلة جداً (مثل طلبك للأكواد)
            
            for i in range(max_wait):
                status = await page.evaluate('''() => {
                    // 1. تحديد حاوية الردود
                    const articles = document.querySelectorAll('article');
                    if (articles.length === 0) return { state: 'waiting' };
                    
                    const lastArticle = articles[articles.length - 1];
                    const markdown = lastArticle.querySelector('.markdown, .prose');
                    
                    // 2. التحقق من وجود مؤشر الكتابة (Streaming)
                    // ChatGPT يضع كلاس 'result-streaming' أو يظهر زر التوقف
                    const isStreaming = !!document.querySelector('.result-streaming, button[aria-label*="Stop"], button[aria-label*="توقف"]');
                    
                    if (markdown && markdown.innerText.trim().length > 0) {
                        if (!isStreaming) {
                            return { state: 'done', html: markdown.innerHTML };
                        }
                        return { state: 'typing' };
                    }
                    return { state: 'waiting' };
                }''')

                if status['state'] == 'done':
                    final_html = status['html']
                    print("✅ اكتمل توليد الرد بنجاح.")
                    break
                elif i % 10 == 0:
                    print(f"⏳ لا يزال ChatGPT يكتب ({i} ثانية)...")
                
                await asyncio.sleep(2) # فحص كل ثانيتين

            if final_html:
                output = {"status": "success", "response": final_html}
            else:
                output = {"status": "error", "message": "انتهت مهلة الانتظار دون الحصول على رد مكتمل"}

    except Exception as e:
        print(f"❌ خطأ فني: {e}")
        output = {"status": "error", "message": str(e)}

    # الحفظ النهائي
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    print("💾 تم تحديث result.json.")

if __name__ == "__main__":
    prompt_arg = sys.argv[1] if len(sys.argv) > 1 else "Hello"
    asyncio.run(run_gpt_automation(prompt_arg))
