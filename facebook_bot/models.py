from django.db import models

from django.utils import timezone

class FacebookAccount(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    cookie_file = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, default='Unknown')  
    last_used = models.DateTimeField(null=True, blank=True) 
    
class BlockedAccount(models.Model):
    email = models.EmailField(unique=True)  # يمنع التكرار في قاعدة البيانات
    reason = models.TextField(blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # يمنع إدخال سجل جديد بنفس الإيميل
        if not BlockedAccount.objects.filter(email=self.email).exists():
            super().save(*args, **kwargs)
        else:
            # ممكن هنا تعملي تحديث بدل تجاهل
            BlockedAccount.objects.filter(email=self.email).update(reason=self.reason)

class LoginRequiredAccount(models.Model):
    email = models.EmailField(unique=True)  # يمنع التكرار
    note = models.TextField(blank=True, null=True)
    date_reported = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not LoginRequiredAccount.objects.filter(email=self.email).exists():
            super().save(*args, **kwargs)
        else:
            LoginRequiredAccount.objects.filter(email=self.email).update(note=self.note)


class FacebookPost(models.Model):
    link = models.URLField()
    text = models.TextField(blank=True, null=True)

class FacebookAction(models.Model):
    ACTION_CHOICES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('like_comment', 'Like and Comment'),
        ('share', 'Share'),
        ('like_comment_share', 'Like, Comment and Share'),
    ]
    link = models.URLField(blank=True, null=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    comment_text = models.TextField(blank=True, null=True)


