
import os
import asyncio
import random
import time
from asgiref.sync import sync_to_async
from django.db import close_old_connections
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from .models import *
import os
from django.utils.timezone import now
COOKIE_DIR = "cookies"  
os.makedirs(COOKIE_DIR, exist_ok=True)


REACTION_MAP = {
    "like": "Like",
    "love": "Love",
    "haha": "Haha",
    "wow": "Wow",
    "sad": "Sad",
    "angry": "Angry"
}

MAX_CONCURRENT_BROWSERS = 5

async def post_async(email, password, post_text="", country=None, image_path=None):
    close_old_connections()

    os.makedirs("cookies", exist_ok=True)
    state_file = os.path.join("cookies", f"{email}_state.json")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = (
            await browser.new_context(storage_state=state_file)
            if os.path.exists(state_file)
            else await browser.new_context()
        )
        page = await context.new_page()

        try:
            await page.goto("https://www.facebook.com")
            await page.wait_for_load_state("load")

            # 🔍 التحقق من الحظر
            try:
                await page.wait_for_selector("text=Your Account Has Been Disabled", timeout=5000)
                print(f"🚫 الحساب {email} محظور")
                await sync_to_async(BlockedAccount.objects.create)(
                    email=email, reason="Facebook disabled this account"
                )
                await browser.close()
                return
            except:
                pass

            # التحقق من تسجيل الدخول
            is_logged_in = False
            try:
                await page.wait_for_selector("//span[contains(text(), \"What's on your mind\")]", timeout=7000)
                is_logged_in = True
            except:
                print(f"⚠️ الحساب {email} يحتاج تسجيل دخول")
                await sync_to_async(LoginRequiredAccount.objects.create)(
                    email=email, note="Session expired or logged out"
                )

            if not is_logged_in:
                await browser.close()
                return

            # ✏️ نشر البوست
            if post_text or image_path:
                try:
                    await page.goto("https://www.facebook.com")
                    await page.wait_for_timeout(5000)
                    await page.locator(
                        "//div[contains(@role, 'button')]//span[contains(text(), \"What's on your mind\")]"
                    ).click(timeout=10000)
                    await page.wait_for_timeout(3000)

                    if post_text:
                        await page.keyboard.type(post_text)

                    if image_path and os.path.exists(image_path):
                        file_inputs = page.locator("form input[type='file']")
                        if await file_inputs.count() > 0:
                            await file_inputs.nth(0).set_input_files(image_path)
                            await page.wait_for_timeout(5000)

                    await page.locator("div[aria-label='Post']").click()
                    print(f"✅ تم نشر البوست من الحساب: {email}")

                except Exception as e:
                    print(f"⚠️ فشل نشر البوست: {e}")
            else:
                print("✅ تم تسجيل الدخول فقط بدون نشر.")

        except Exception as e:
            print(f"❌ خطأ عام: {e}")

        await browser.close()

        
async def facebook_action(email, password, post_url, action, comment_text=None):
    state_file = os.path.join(COOKIE_DIR, f"{email}_state.json")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(storage_state=state_file) if os.path.exists(state_file) else await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.facebook.com")
        await page.wait_for_load_state("domcontentloaded")
  

        try:
            await page.wait_for_selector("text=Your Account Has Been Disabled", timeout=5000)
            print(f"🚫 الحساب {email} محظور")
            await sync_to_async(BlockedAccount.objects.create)(
                email=email, reason="Facebook disabled this account"
            )
            await browser.close()
            return
        except:
            pass

        # التحقق من تسجيل الدخول
        is_logged_in = False
        try:
            await page.wait_for_selector("//span[contains(text(), \"What's on your mind\")]", timeout=7000)
            is_logged_in = True
        except:
            print(f"⚠️ الحساب {email} يحتاج تسجيل دخول")
            await sync_to_async(LoginRequiredAccount.objects.create)(
                email=email, note="Session expired or logged out"
            )

        if not is_logged_in:
            await browser.close()
            return


        print(f"🔗 فتح البوست: {post_url}")
        await page.goto(post_url)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(2000)

        # تنفيذ الأكشن اللايك
        if action in ["like", "like_comment", "like_comment_share"]:
            like_buttons = page.locator('div[aria-label="Like"][role="button"]')
            if await like_buttons.count() >= 2:
                try:
                    await like_buttons.nth(1).click()
                    print("👍 تم الضغط على زر اللايك")
                except Exception as e:
                    print(f"⚠️ خطأ عند الضغط على اللايك: {e}")
            else:
                print("❌ لم يتم العثور على زر اللايك الثاني")

        # تنفيذ الأكشن الكومنت
        if action in ["comment", "like_comment", "like_comment_share"] and comment_text:
            try:
                comment_box = page.locator(
                    'div[aria-label="Write a comment…"], div[aria-label="Write a public comment…"], div[aria-label="Submit your first comment…"]'
                ).first
                await comment_box.click()
                await page.keyboard.type(comment_text)
                await page.keyboard.press("Enter")
                print("💬 تم إضافة التعليق")
            except Exception as e:
                print(f"⚠️ فشل في إضافة التعليق: {e}")

        if action in ["share", "like_comment_share"]:
            try:
                # تحديد جميع أزرار المشاركة المحتملة (لو في أكثر من زر)
                share_buttons = page.locator('div[aria-label="Send this to friends or post it on your profile."]')
                
                count = await share_buttons.count()
                if count == 0:
                    # لو مفيش زر بهذا الـ aria-label جرب الزر بناء على span نص Share
                    share_buttons = page.locator('span[data-ad-rendering-role="share_button"]')
                    count = await share_buttons.count()
                    print(f"🔄 عدد أزرار المشاركة المتاحة: {count}")
                if count == 0:
                    print("❌ لم أجد أي زر مشاركة")
                    return
                
                # نختار الزر الثاني مثل اللايك (لو موجود)
                index_to_click = 1 if count > 1 else 0
                share_button = share_buttons.nth(index_to_click)
                
                await share_button.scroll_into_view_if_needed()
                await page.wait_for_timeout(300)
                await share_button.click()
                print(f"🔄 تم الضغط على زر المشاركة رقم {index_to_click + 1}")
                
                await page.wait_for_timeout(2000)

                # محاولة الضغط على زر "Share now (Public)"
                share_now_button = page.locator('div[aria-label="Share now"]').first
                if await share_now_button.count():
                    await share_now_button.click()
                    print("🔄 تم مشاركة البوست مباشرة")
                else:
                    post_button = page.locator('div[aria-label="Post"]').first
                    if await post_button.count():
                        await post_button.click()
                        print("🔄 تم مشاركة البوست")
                    else:
                        print("❌ لم أجد زر لإتمام المشاركة")

                await page.wait_for_timeout(3000)

            except Exception as e:
                print(f"⚠️ فشل في المشاركة: {e}")




        await browser.close()



async def send_friend_requests(email, password, country, search_name, max_requests_per_account=5):
    state_file = os.path.join("cookies", f"{email}_state.json")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await (browser.new_context(storage_state=state_file) if os.path.exists(state_file) else browser.new_context())
        page = await context.new_page()

        # تسجيل دخول إذا مافيش كوكيز
        await page.goto("https://www.facebook.com")
        await page.wait_for_load_state("domcontentloaded")
  

        try:
            await page.wait_for_selector("text=Your Account Has Been Disabled", timeout=5000)
            print(f"🚫 الحساب {email} محظور")
            await sync_to_async(BlockedAccount.objects.create)(
                email=email, reason="Facebook disabled this account"
            )
            await browser.close()
            return
        except:
            pass

        # التحقق من تسجيل الدخول
        is_logged_in = False
        try:
            await page.wait_for_selector("//span[contains(text(), \"What's on your mind\")]", timeout=7000)
            is_logged_in = True
        except:
            print(f"⚠️ الحساب {email} يحتاج تسجيل دخول")
            await sync_to_async(LoginRequiredAccount.objects.create)(
                email=email, note="Session expired or logged out"
            )

        if not is_logged_in:
            await browser.close()
            return

        # البحث عن الأشخاص
        search_url = f"https://www.facebook.com/search/people/?q={search_name}"
        await page.goto(search_url)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(3000)

        # تطبيق فلتر البلد / المدينة
        city_input = page.locator('input[aria-label="City"], input[placeholder="City"]')
        await city_input.click()
        await city_input.fill(country)
        await page.wait_for_timeout(2000)

        # اختيار أول اقتراح
        listbox = page.locator('[role="listbox"] >> div:has-text("' + country + '")')
        count = await listbox.count()

        if count > 0:
            print(f"✅ لقيت {count} اختيار في قايمة البلد")
            await listbox.nth(0).click()  # اختار أول اختيار
        else:
            print(f"⚠️ مفيش أي اختيار مطابق ل {country}")
            await browser.close()
            return

        await page.wait_for_timeout(3000)

        # البحث عن أزرار Add Friend
        add_buttons = page.locator('div[aria-label="Add friend"][role="button"]')
        total = await add_buttons.count()

        if total == 0:
            print(f"❌ لم يتم العثور على أي أشخاص مع البحث '{search_name}' في '{country}'.")
            await browser.close()
            return

        num_requests = random.randint(1, min(max_requests_per_account, total))
        print(f"📨 {email} - إرسال {num_requests} طلبات صداقة...")

        for i in range(num_requests):
            try:
                await add_buttons.nth(i).click()
                print(f"✅ {email} - تم إرسال طلب الصداقة رقم {i+1}")
                await asyncio.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"⚠️ {email} - فشل في إرسال الطلب رقم {i+1}: {e}")

        await browser.close()

        # تحديث وقت الاستخدام الأخير
        account = await sync_to_async(FacebookAccount.objects.get)(email=email)
        account.last_used = now()
        await sync_to_async(account.save)()

async def rate_page_async(email, password, page_url, review_text , recommend=True):
    close_old_connections()
    os.makedirs("cookies", exist_ok=True)
    state_file = os.path.join("cookies", f"{email}_state.json")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = (
            await browser.new_context(storage_state=state_file)
            if os.path.exists(state_file)
            else await browser.new_context()
        )
        page = await context.new_page()

        await page.goto("https://www.facebook.com")
        await page.wait_for_load_state("domcontentloaded")
  

        try:
            await page.wait_for_selector("text=Your Account Has Been Disabled", timeout=5000)
            print(f"🚫 الحساب {email} محظور")
            await sync_to_async(BlockedAccount.objects.create)(
                email=email, reason="Facebook disabled this account"
            )
            await browser.close()
            return
        except:
            pass

        # التحقق من تسجيل الدخول
        is_logged_in = False
        try:
            await page.wait_for_selector("//span[contains(text(), \"What's on your mind\")]", timeout=7000)
            is_logged_in = True
        except:
            print(f"⚠️ الحساب {email} يحتاج تسجيل دخول")
            await sync_to_async(LoginRequiredAccount.objects.create)(
                email=email, note="Session expired or logged out"
            )

        if not is_logged_in:
            await browser.close()
            return

        try:
            await page.goto(page_url)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(4000)

            # 1- افتح تبويب Reviews
            try:
                reviews_tab = page.locator("a[role='tab']", has_text="Reviews")
                if await reviews_tab.count() > 0:
                    await reviews_tab.first.click()
                    await page.wait_for_timeout(3000)
            except:
                print("⚠️ Reviews tab مش موجود")

            # 2- اختار Yes (أو No)
            try:
                if recommend:
                    btn = page.locator('div[role="button"][aria-label="Yes"]')
                else:
                    btn = page.locator('div[role="button"][aria-label="No"]')

                if await btn.count() > 0:
                    await btn.first.click()
                    await page.wait_for_timeout(2000)
            except:
                print("⚠️ زر Yes/No مش لقيته")

    
    
            try:
                # 🔹 افتح زر تغيير الخصوصية (جنب مكان كتابة الريفيو)
                privacy_btn = page.locator('div[role="button"][aria-label*="Sharing with"]')

                if await privacy_btn.count() > 0:
                    await privacy_btn.first.click()
                    print("✅ فتحت قائمة الخصوصية")
                    await page.wait_for_timeout(2000)

                    # 🔹 دور على خيار Public بالـ text
                    public_option = page.locator('//div[@role="radio"]//span[text()="Public"]')

                    if await public_option.count() > 0:
                        await public_option.first.click()
                        await page.wait_for_timeout(1500)
                        print("✅ الخصوصية اتغيرت لـ Public")
                    else:
                        print("⚠️ مش لاقي خيار Public - احتمال Facebook مغير الـ DOM")
                    done_option = page.locator('div[role="button"][aria-label*="Done"]')

                    if await done_option.count() > 0:
                        await done_option.first.click()
                        await page.wait_for_timeout(1500)
                        print("✅ الخصوصية اتغيرت لـ done_option")
                else:
                    print("⚠️ مش لاقيت زر الخصوصية")

            except Exception as e:
                print(f"❌ خطأ في تغيير الخصوصية: {e}")

            textbox = page.locator('div[role="textbox"][aria-placeholder*="recommend"]')
            if await textbox.count() == 0:
                # fallback: التاني غالبًا بيكون الريفيو (الأول كومنت)
                textbox = page.locator('div[role="textbox"]').nth(1)

            print(f"✅ لقيت مربع الريفيو: {await textbox.count()}")

            if await textbox.count() > 0:
                await textbox.first.type(str(review_text), delay=50)
                await page.wait_for_timeout(1000)
                print("✅ الريفيو اتكتب فعلياً في الفورم المفتوحة")
            else:
                print("⚠️ مربع كتابة الريفيو مش لقيته")


            # 4- اضغط Post
            try:
                post_btn = page.locator("div[role='button']", has_text="Post")
                if await post_btn.count() > 0:
                    await post_btn.first.click()
                    await page.wait_for_timeout(5000)
            except:
                print("⚠️ زر Post مش لقيته")

            print(f"✅ {email} كتب ريفيو على {page_url}")
        except Exception as e:
            print(f"❌ خطأ عام: {e}")
        await page.wait_for_timeout(5000)
        await browser.close()




async def bulk_wrapper(semaphore, func, *args):
    async with semaphore:
        await func(*args)

async def bulk_action(account_ids, func, *args):
    accounts = await sync_to_async(list)(
        FacebookAccount.objects.filter(id__in=account_ids)
    )
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)
    tasks = [
        bulk_wrapper(semaphore, func, acc.email, acc.password, *args)
        for acc in accounts
    ]
    await asyncio.gather(*tasks)

