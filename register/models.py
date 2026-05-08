
from django.db import models

from django.contrib.auth.models import User

from django.db.models.signals import post_save

from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model


class UserProfile(models.Model):
    user                      = models.OneToOneField(
                                   settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE
                               )
    auto_compute_permission   = models.BooleanField(default=False)
    database_permission       = models.BooleanField(default=True)
    ml_prediction_permission  = models.BooleanField(default=True)
    gaussian_permission  = models.BooleanField(default=False)
    
    
    daily_task_limit = models.PositiveIntegerField(
        default=3,
        verbose_name="Daily Task Limit",
        help_text="Maximum number of tasks the user can run per day (non-negative integer)."
    )


class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    phone = models.CharField(max_length=20, blank=True)
    
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)
    
    bio = models.TextField(max_length=500, blank=True)
    
    calculating_authority = models.BooleanField(default=True)

    def __str__(self):
        return 'user {}'.format(self.user.username)




@receiver(post_save, sender=get_user_model())
def create_user_profile(sender,instance, created,**kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserProfile.objects.create(user=instance)



@receiver(post_save, sender=get_user_model())
def save_user_profile(sender,instance,**kwargs):
    instance.profile.save()


from django.db import models

class Captcha(models.Model):
    
    code = models.CharField(max_length=10)
    
    expire_time = models.DateTimeField()
    
    encrypt_id = models.CharField(max_length=100)

    def __str__(self):
        return f'Captcha {self.encrypt_id} - Expires at {self.expire_time}'

