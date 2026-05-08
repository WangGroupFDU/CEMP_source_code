

from django import forms


from django.contrib.auth.models import User
from django.forms import ModelForm
from .models import Profile
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from register.models import UserProfile
from django.utils import timezone
from datetime import timedelta
import re


def validate_email_domain(email):
    """
    Email validation function with limited authorization domains and full authorization patterns.
    All domains are allowed, but some have limited functionality.
    """
    
    limited_auth_domains = ["126.com", "163.com", "qq.com", "gmail.com", "outlook.com"]

    
    domain = email.split("@")[-1].lower()

    
    full_auth_patterns = [
        r".*\.edu\..*",  
        r".*\.mil\..*",  
        r".*\.gov\..*",  
    ]

    
    for pattern in full_auth_patterns:
        if re.match(pattern, domain):
            return email

    
    if domain in limited_auth_domains:
        
        
        return email

    
    return email



class UserLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        
        fields = (
            "auto_compute_permission",
            "database_permission",
            "ml_prediction_permission",
        )
        
        widgets = {
            "auto_compute_permission": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "database_permission": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "ml_prediction_permission": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }



UserProfileFormSet = modelformset_factory(
    UserProfile,
    form=UserProfileForm,
    extra=0,  
    can_delete=False,  
)


class UserProfileFilterForm(forms.Form):

    BOOLEAN_FILTER_CHOICES = (
        ("all", "All"),
        ("true", "Enabled"),
        ("false", "Disabled"),
    )

    q = forms.CharField(required=False, max_length=150)
    auto_compute_permission = forms.ChoiceField(
        required=False,
        choices=BOOLEAN_FILTER_CHOICES,
        initial="all",
    )
    gaussian_permission = forms.ChoiceField(
        required=False,
        choices=BOOLEAN_FILTER_CHOICES,
        initial="all",
    )
    database_permission = forms.ChoiceField(
        required=False,
        choices=BOOLEAN_FILTER_CHOICES,
        initial="all",
    )
    ml_prediction_permission = forms.ChoiceField(
        required=False,
        choices=BOOLEAN_FILTER_CHOICES,
        initial="all",
    )


class UserProfileRowUpdateForm(forms.Form):

    profile_id = forms.IntegerField(min_value=1)
    auto_compute_permission = forms.BooleanField(required=False)
    gaussian_permission = forms.BooleanField(required=False)
    database_permission = forms.BooleanField(required=False)
    ml_prediction_permission = forms.BooleanField(required=False)
    daily_task_limit = forms.IntegerField(min_value=0)



class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email")

    class Meta:
        
        model = User
        
        fields = ["id", "username", "email"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        try:
            existing_user = User.objects.get(username=username)
            if not existing_user.is_active:
                
                expire_threshold = timezone.now() - timedelta(days=3)
                if existing_user.date_joined < expire_threshold:
                    existing_user.delete()
                    return username
                else:
                    raise ValidationError(
                        "此用户名已注册但尚未激活，请检查邮箱中的激活链接。"
                        "This username is registered but not yet activated."
                    )
            
        except User.DoesNotExist:
            pass
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")

        
        validate_email_domain(email)

        try:
            existing_user = User.objects.get(email=email)
            if not existing_user.is_active:
                
                expire_threshold = timezone.now() - timedelta(days=3)
                if existing_user.date_joined < expire_threshold:
                    existing_user.delete()
                    return email
                else:
                    raise ValidationError(
                        "此邮箱已注册但尚未激活，请检查邮箱中的激活链接。"
                        "This email is registered but not yet activated."
                    )
            else:
                raise ValidationError("This email has been registered")
        except User.DoesNotExist:
            pass
        return email



class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "avatar", "bio")


class EmailModifyForm(forms.Form):
    new_email = forms.EmailField(label="New Email Address")
    password = forms.CharField(widget=forms.PasswordInput, label="Current Password")

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_email(self):
        new_email = self.cleaned_data.get("new_email")

        
        validate_email_domain(new_email)

        if User.objects.filter(email=new_email).exists():
            raise ValidationError("该邮箱已被注册")
        return new_email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.user and not self.user.check_password(password):
            raise ValidationError("当前密码不正确")
        return password
