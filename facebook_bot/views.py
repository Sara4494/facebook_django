from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FacebookAccount, FacebookPost, FacebookAction
from .bot import  *
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
from django.utils.timezone import now
import asyncio
from rest_framework.views import APIView
import os
import shutil
from django.utils.timezone import now
from random import sample

COOKIE_DIR = "cookies"
os.makedirs(COOKIE_DIR, exist_ok=True)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FacebookAccount

class CountryListAPIView(APIView):
    def get(self, request):
        try:
            countries = FacebookAccount.objects.values_list("country", flat=True).distinct()
            return Response({"countries": list(countries)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FacebookActionAPIView(APIView):
    def post(self, request):
        link = request.data.get('link')
        comment_text = request.data.get('comment_text', '')
        country = request.data.get('country', None)
        count = int(request.data.get('count', 1))
        action = request.data.get('action')  

        if not link or not country or not action:
            return Response({'error': 'link, country, and action are required'}, status=status.HTTP_400_BAD_REQUEST)

        # جلب الحسابات حسب البلد وترتيب أقل last_used أولاً
        accounts_qs = FacebookAccount.objects.filter(country=country).order_by('last_used')
        accounts_never_used = accounts_qs.filter(last_used__isnull=True)
        accounts_used = accounts_qs.filter(last_used__isnull=False)
        candidates = list(accounts_never_used) + list(accounts_used)

        actual_count = min(count, len(candidates))
        if actual_count == 0:
            return Response({'error': 'No available accounts for this country'}, status=status.HTTP_400_BAD_REQUEST)

        selected_accounts = sample(candidates, actual_count)

        success = []
        failed = []

        async def run_all():
            tasks = []
            for account in selected_accounts:
                tasks.append(
                    facebook_action(
                        account.email,
                        account.password,
                        link,
                        action,
                        comment_text if action in ["comment", "like_comment", "like_comment_share"] else None
                    )
                )
                success.append(account.email)
            await asyncio.gather(*tasks)

            # تحديث last_used للحسابات اللي استخدمت
            for account in selected_accounts:
                account.last_used = now()
                await sync_to_async(account.save)()

        from asgiref.sync import async_to_sync
        async_to_sync(run_all)()

        return Response({
            'message': f'Action "{action}" started for {actual_count} accounts in {country}',
            'success': success,
            'failed': failed,
        }, status=status.HTTP_200_OK)


class FacebookPostTextAPIView(APIView):
    def post(self, request):
        text = request.data.get('text')
        image_path = request.data.get('image_path')
        country = request.data.get('country', None)
        count = int(request.data.get('count', 1))  

        if not text and not image_path:
            return Response({'error': 'You must provide either text or image_path'}, status=status.HTTP_400_BAD_REQUEST)
        if not country:
            return Response({'error': 'country is required'}, status=status.HTTP_400_BAD_REQUEST)

        # جلب الحسابات حسب البلد مرتبة بأقل last_used (يعني اللي ما استخدمتش من فترة طويلة)
        accounts_qs = FacebookAccount.objects.filter(country=country).order_by('last_used')

        accounts_never_used = accounts_qs.filter(last_used__isnull=True)
        accounts_used = accounts_qs.filter(last_used__isnull=False)

        candidates = list(accounts_never_used) + list(accounts_used)

        actual_count = min(count, len(candidates))  

        selected_accounts = sample(candidates, actual_count)

        async def run_all():
            tasks = []
            for account in selected_accounts:
                tasks.append(post_async(
                    account.email,
                    account.password,
                    text or "",
                    account.country,
                    image_path
                ))
            await asyncio.gather(*tasks)

            for account in selected_accounts:
                account.last_used = now()
                await sync_to_async(account.save)()

        from asgiref.sync import async_to_sync
        async_to_sync(run_all)()

        return Response({'message': f'Post publish attempt started for {actual_count} accounts in {country}'}, status=status.HTTP_200_OK)



class FacebookPageRatingAPIView(APIView):
    def post(self, request):
        link = request.data.get("link")
        review_text = request.data.get("review_text")
        country = request.data.get("country")
        count = int(request.data.get("count", 1))

        if not link or not country:
            return Response({"error": "link and country are required"}, status=status.HTTP_400_BAD_REQUEST)

        accounts_qs = FacebookAccount.objects.filter(country=country).order_by('last_used')
        accounts_never_used = accounts_qs.filter(last_used__isnull=True)
        accounts_used = accounts_qs.filter(last_used__isnull=False)
        candidates = list(accounts_never_used) + list(accounts_used)

        actual_count = min(count, len(candidates))
        if actual_count == 0:
            return Response({'error': 'No available accounts for this country'}, status=status.HTTP_400_BAD_REQUEST)

        selected_accounts = sample(candidates, actual_count)
        success = []

        async def run_all():
            tasks = []
            for account in selected_accounts:
                tasks.append(
                    rate_page_async(account.email, account.password, link, review_text)
                )
                success.append(account.email)

            await asyncio.gather(*tasks)

            # تحديث الـ last_used
            for account in selected_accounts:
                account.last_used = now()
                await sync_to_async(account.save)()

        async_to_sync(run_all)()

        return Response({
            "message": f"Rating page {link} with {review_text} stars started for {actual_count} accounts",
            "success": success
        }, status=status.HTTP_200_OK)


import shutil
class FacebookLoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        country = request.data.get('country', 'Unknown')
        cookie_file_path = request.data.get('cookie_file', '')

        if not email or not password:
            return Response({'error': 'Email and password are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            saved_cookie_path = ""
            if cookie_file_path and os.path.exists(cookie_file_path):
                # اسم الملف الجديد جوة مجلد cookies
                saved_cookie_path = os.path.join(COOKIE_DIR, f"{email}_state.json")
                shutil.copy(cookie_file_path, saved_cookie_path)  # نسخ الملف

            account, created = FacebookAccount.objects.update_or_create(
                email=email,
                defaults={
                    'password': password,
                    'cookie_file': saved_cookie_path,
                    'country': country
                }
            )

            return Response({
                'message': 'Account saved successfully',
                'account_id': account.id,
                'created': created,
                'country': account.country,
                'cookie_file': account.cookie_file
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print("❌ خطأ أثناء حفظ البيانات:")
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class SendFriendRequestsAPIView(APIView):
    def post(self, request):
        search_name = request.data.get('search_name', '').strip()
        country = request.data.get('country', '').strip()
        count = int(request.data.get('count', 1))
        max_requests_per_account = int(request.data.get('max_requests_per_account', 5))

        if not search_name:
            return Response({'error': 'search_name is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not country:
            return Response({'error': 'country is required'}, status=status.HTTP_400_BAD_REQUEST)

        # جلب الحسابات حسب البلد وترتيب أقل last_used أولاً
        accounts_qs = FacebookAccount.objects.filter(country=country).order_by('last_used')
        accounts_never_used = accounts_qs.filter(last_used__isnull=True)
        accounts_used = accounts_qs.filter(last_used__isnull=False)
        candidates = list(accounts_never_used) + list(accounts_used)

        actual_count = min(count, len(candidates))
        if actual_count == 0:
            return Response({'error': 'No available accounts for this country'}, status=status.HTTP_400_BAD_REQUEST)

        selected_accounts = random.sample(candidates, actual_count)

        async def run_all():
            semaphore = asyncio.Semaphore(3)  # عدد المتصفحات المفتوحة بالتوازي
            async def wrapper(email, password):
                async with semaphore:
                    await send_friend_requests(email, password, country, search_name, max_requests_per_account)

            tasks = [
                wrapper(acc.email, acc.password)
                for acc in selected_accounts
            ]
            await asyncio.gather(*tasks)

            # تحديث last_used لجميع الحسابات
            for acc in selected_accounts:
                acc.last_used = now()
                await sync_to_async(acc.save)()

        async_to_sync(run_all)()

        return Response({
            'message': f'Friend requests sending started for {actual_count} accounts searching "{search_name}" in {country}'
        }, status=status.HTTP_200_OK)