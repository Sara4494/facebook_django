from django.urls import path
from .views import (
    FacebookActionAPIView,
    SendFriendRequestsAPIView,
    FacebookLoginAPIView,
    FacebookPostTextAPIView,
    FacebookPageRatingAPIView,
    CountryListAPIView
)

urlpatterns = [
    # path('accounts/add/', FacebookAccountCreateAPIView.as_view()),
    # path('accounts/search/', FacebookAccountSearchAPIView.as_view()),
    # path('posts/add/', FacebookPostCreateAPIView.as_view()),
  
    path('facebook-action/', FacebookActionAPIView.as_view()),
    path('posts/text/', FacebookPostTextAPIView.as_view()),
    path('accounts/login/', FacebookLoginAPIView.as_view()),
    path('friend-requests/', SendFriendRequestsAPIView.as_view()),
    path('rate-page/', FacebookPageRatingAPIView.as_view()),
    
    path('countries/', CountryListAPIView.as_view()),



]
