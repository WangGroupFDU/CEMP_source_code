from django.shortcuts import render


from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied


from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.urls import reverse

from .forms import (
    UserLoginForm,
    UserRegisterForm,
    ProfileForm,
    EmailModifyForm,
    UserProfileFilterForm,
    UserProfileRowUpdateForm,
)
from .models import Profile
from .models import UserProfile


from django.core.mail import send_mail


import random
import string


from smtplib import SMTPAuthenticationError, SMTPRecipientsRefused

import logging

logger = logging.getLogger("django")

from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import json


def _ensure_staff_user(request):

    if not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied("Only staff users can manage permissions.")


def _apply_boolean_filter(queryset, field_name, value):

    if value == "true":
        return queryset.filter(**{field_name: True})
    if value == "false":
        return queryset.filter(**{field_name: False})
    return queryset


def _build_user_profile_admin_queryset(filter_form):

    queryset = (
        UserProfile.objects.select_related("user")
        .annotate(task_count=Count("user__computetask", distinct=True))
        .order_by("-user__date_joined", "user__username")
    )

    cleaned = filter_form.cleaned_data
    query_text = (cleaned.get("q") or "").strip()
    if query_text:
        queryset = queryset.filter(
            Q(user__username__icontains=query_text) | Q(user__email__icontains=query_text)
        )

    queryset = _apply_boolean_filter(
        queryset,
        "auto_compute_permission",
        cleaned.get("auto_compute_permission", "all"),
    )
    queryset = _apply_boolean_filter(
        queryset,
        "gaussian_permission",
        cleaned.get("gaussian_permission", "all"),
    )
    queryset = _apply_boolean_filter(
        queryset,
        "database_permission",
        cleaned.get("database_permission", "all"),
    )
    queryset = _apply_boolean_filter(
        queryset,
        "ml_prediction_permission",
        cleaned.get("ml_prediction_permission", "all"),
    )

    return queryset


def _get_user_profile_admin_stats():

    return UserProfile.objects.aggregate(
        total_users=Count("id"),
        auto_compute_users=Count("id", filter=Q(auto_compute_permission=True)),
        gaussian_users=Count("id", filter=Q(gaussian_permission=True)),
        database_users=Count("id", filter=Q(database_permission=True)),
        ml_prediction_users=Count("id", filter=Q(ml_prediction_permission=True)),
    )


@login_required(login_url="/register/login/")
def user_profile_admin_view(request):

    _ensure_staff_user(request)

    redirect_query = request.POST.get("return_query", "").strip()

    if request.method == "POST":
        action_type = request.POST.get("action_type", "").strip()
        redirect_url = reverse("register:user_profile_admin")
        if redirect_query:
            redirect_url = f"{redirect_url}?{redirect_query}"

        if action_type == "single_update":
            form = UserProfileRowUpdateForm(request.POST)
            if form.is_valid():
                try:
                    profile = UserProfile.objects.select_related("user").get(
                        pk=form.cleaned_data["profile_id"]
                    )
                except UserProfile.DoesNotExist:
                    messages.error(request, "The selected user profile does not exist.")
                    return redirect(redirect_url)
                profile.auto_compute_permission = form.cleaned_data[
                    "auto_compute_permission"
                ]
                profile.gaussian_permission = form.cleaned_data["gaussian_permission"]
                profile.database_permission = form.cleaned_data["database_permission"]
                profile.ml_prediction_permission = form.cleaned_data[
                    "ml_prediction_permission"
                ]
                profile.daily_task_limit = form.cleaned_data["daily_task_limit"]
                profile.save(
                    update_fields=[
                        "auto_compute_permission",
                        "gaussian_permission",
                        "database_permission",
                        "ml_prediction_permission",
                        "daily_task_limit",
                    ]
                )
                messages.success(
                    request,
                    f"Updated permissions for {profile.user.username}.",
                )
            else:
                messages.error(request, "Single-user update failed. Please check the submitted values.")
            return redirect(redirect_url)

        if action_type in {"batch_permission", "batch_daily_limit"}:
            selected_profile_ids = request.POST.getlist("selected_profiles")
            if not selected_profile_ids:
                messages.error(request, "Please select at least one user for batch operations.")
                return redirect(redirect_url)

            queryset = UserProfile.objects.filter(pk__in=selected_profile_ids)
            if action_type == "batch_permission":
                permission_field = request.POST.get("permission_field", "").strip()
                permission_value = request.POST.get("permission_value", "").strip()
                allowed_fields = {
                    "auto_compute_permission",
                    "gaussian_permission",
                    "database_permission",
                    "ml_prediction_permission",
                }
                if permission_field not in allowed_fields or permission_value not in {
                    "enable",
                    "disable",
                }:
                    messages.error(request, "Invalid batch permission operation.")
                    return redirect(redirect_url)

                queryset.update(**{permission_field: permission_value == "enable"})
                messages.success(
                    request,
                    f"Batch updated {queryset.count()} user profiles.",
                )
                return redirect(redirect_url)

            try:
                daily_task_limit = int(request.POST.get("batch_daily_task_limit", "").strip())
                if daily_task_limit < 0:
                    raise ValueError
            except ValueError:
                messages.error(request, "Daily task limit must be a non-negative integer.")
                return redirect(redirect_url)

            queryset.update(daily_task_limit=daily_task_limit)
            messages.success(
                request,
                f"Updated daily task limit for {queryset.count()} user profiles.",
            )
            return redirect(redirect_url)

        messages.error(request, "Unknown operation.")
        return redirect(reverse("register:user_profile_admin"))

    filter_form = UserProfileFilterForm(request.GET or None)
    if not filter_form.is_valid():
        filter_form = UserProfileFilterForm(
            {
                "q": "",
                "auto_compute_permission": "all",
                "gaussian_permission": "all",
                "database_permission": "all",
                "ml_prediction_permission": "all",
            }
        )
        filter_form.is_valid()

    profiles = _build_user_profile_admin_queryset(filter_form)

    context = {
        "filter_form": filter_form,
        "profiles": profiles,
        "stats": _get_user_profile_admin_stats(),
        "current_query": request.GET.urlencode(),
        "focus_profile": request.GET.get("focus_profile", "").strip(),
        "show_admin": True,
    }
    return render(request, "register/user_profile_admin.html", context)


def user_login(request):
    from django.http import JsonResponse
    from rest_framework.authtoken.models import Token

    if request.method == "POST":
        
        is_json_api = request.content_type == "application/json"

        if is_json_api:
            try:
                
                body = (
                    request.body.decode("utf-8")
                    if isinstance(request.body, bytes)
                    else request.body
                )
                json_data = json.loads(body)
                data_source = json_data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"JSON解析失败: {str(e)}, body: {request.body}")
                return JsonResponse(
                    {"success": False, "error": f"Invalid JSON: {str(e)}"}, status=400
                )
        else:
            data_source = request.POST

        user_login_form = UserLoginForm(data=data_source)

        if user_login_form.is_valid():
            
            data = user_login_form.cleaned_data

            
            
            
            try:
                existing_user = User.objects.get(username=data["username"])
                if not existing_user.is_active:
                    
                    if existing_user.check_password(data["password"]):
                        logger.warning(
                            f"未激活用户尝试登录: {existing_user.username} ({existing_user.email})"
                        )
                        
                        if (
                            request.headers.get("X-Requested-With") == "XMLHttpRequest"
                            or request.content_type == "application/json"
                        ):
                            return JsonResponse(
                                {
                                    "success": False,
                                    "error": "您的账号尚未激活，请检查注册邮箱中的激活邮件",
                                    "not_activated": True,
                                    "email": existing_user.email,
                                },
                                status=403,
                            )
                        else:
                            return HttpResponse(
                                "Your account has not been activated. Please check the activation email in your registered mailbox and click the activation link."
                            )
            except User.DoesNotExist:
                pass  

            
            
            user = authenticate(username=data["username"], password=data["password"])

            if user:
                
                login(request, user)

                
                is_api_request = (
                    request.headers.get("X-Requested-With") == "XMLHttpRequest"
                    or request.content_type == "application/json"
                )

                if is_api_request:
                    
                    
                    token, created = Token.objects.get_or_create(user=user)

                    
                    try:
                        from .models import UserProfile

                        user_profile = UserProfile.objects.get(user=user)
                        permissions = {
                            "auto_compute_permission": user_profile.auto_compute_permission,
                            "database_permission": user_profile.database_permission,
                            "ml_prediction_permission": user_profile.ml_prediction_permission,
                            "gaussian_permission": user_profile.gaussian_permission,
                            "daily_task_limit": user_profile.daily_task_limit,
                        }
                    except:
                        permissions = {}

                    return JsonResponse(
                        {
                            "success": True,
                            "token": token.key,
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "email": user.email,
                                "permissions": permissions,
                            },
                            "message": "登录成功",
                        }
                    )
                else:
                    
                    return redirect("home:homepage")
            else:
                
                if (
                    request.headers.get("X-Requested-With") == "XMLHttpRequest"
                    or request.content_type == "application/json"
                ):
                    
                    return JsonResponse(
                        {
                            "success": False,
                            "error": "Username or password is incorrect",
                        },
                        status=401,
                    )
                else:
                    
                    return HttpResponse("Username or password is incorrect")
        else:
            
            if (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.content_type == "application/json"
            ):
                
                errors = {}
                for field, field_errors in user_login_form.errors.items():
                    errors[field] = [str(err) for err in field_errors]
                return JsonResponse({"success": False, "errors": errors}, status=400)
            else:
                
                return HttpResponse("用户名或密码输入不合法")
    elif request.method == "GET":
        user_login_form = UserLoginForm()
        return render(request, "login.html")
    else:
        return HttpResponse("请使用GET或者POST请求")


def user_logout(request):
    from django.http import JsonResponse
    from rest_framework.authtoken.models import Token

    
    is_api_request = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.content_type == "application/json"
        or request.headers.get("Authorization", "").startswith("Token")
    )

    if is_api_request:
        

        
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Token "):
            token_key = auth_header.split(" ")[1]
            try:
                token = Token.objects.get(key=token_key)
                token.delete()  
                logger.info(f"Token已删除: {token_key[:10]}...")
            except Token.DoesNotExist:
                logger.warning(f"Token不存在: {token_key[:10]}...")

        
        if request.user.is_authenticated:
            try:
                Token.objects.filter(user=request.user).delete()
            except Exception as e:
                logger.error(f"删除用户Token失败: {str(e)}")

        
        logout(request)

        return JsonResponse({"success": True, "message": "注销成功"})
    else:
        
        logout(request)
        return redirect("home:homepage")




def user_register(request):
    from django.http import JsonResponse
    from rest_framework.authtoken.models import Token
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import send_mail, EmailMessage, get_connection
    from django.conf import settings
    from .tokens import activation_token

    if request.method == "POST":
        
        if request.content_type == "application/json":
            try:
                body = (
                    request.body.decode("utf-8")
                    if isinstance(request.body, bytes)
                    else request.body
                )
                json_data = json.loads(body)
                data_source = json_data
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"JSON解析失败: {str(e)}, body: {request.body}")
                return JsonResponse(
                    {"success": False, "error": f"Invalid JSON: {str(e)}"}, status=400
                )
        else:
            data_source = request.POST

        user_register_form = UserRegisterForm(data=data_source)
        print(user_register_form.is_valid())
        error = user_register_form.errors
        print(user_register_form.errors)
        print(str(user_register_form["username"]))
        print(str(user_register_form["email"]))
        print(str(user_register_form["password1"]))
        print(str(user_register_form["password2"]))

        if user_register_form.is_valid():
            
            new_user = user_register_form.save(commit=False)
            new_user.is_active = False  
            new_user.save()

            
            
            logger.debug("index page")
            logger.info("start a new user registration: " + new_user.username)
            
            
            uidb64 = urlsafe_base64_encode(force_bytes(new_user.pk))
            token = activation_token.make_token(new_user)

            
            activation_link = (
                f"{settings.SITE_DOMAIN}/register/activate?uid={uidb64}&token={token}"
            )

            
            user_email = new_user.email
            subject = "激活您的CEMP账号 - Activate Your CEMP Account"
            message = f"""
您好 {new_user.username}，

感谢您注册CEMP（清洁能源材料平台）！

请点击下面的链接激活您的账号：
{activation_link}

此链接将在3天后过期。

如果您没有注册CEMP账号，请忽略此邮件。

---
Hello {new_user.username},

Thank you for registering on CEMP (Clean Energy Materials Platform)!

Please click the link below to activate your account:
{activation_link}

This link will expire in 3 days.

If you did not register for a CEMP account, please ignore this email.

CEMP Team
"""

            try:
                
                connection = get_connection(
                    host="smtp.qq.com",
                    port=465,
                    username="user@example.com",
                    password="<CHANGE_ME_SMTP_PASSWORD>",
                    use_ssl=True,
                    use_tls=False,
                )
                email_message = EmailMessage(
                    subject,
                    message,
                    "user@example.com",  
                    [user_email],
                    connection=connection,
                )
                email_message.send(fail_silently=False)
                logger.info(
                    f"激活邮件已发送到: {user_email}, 用户: {new_user.username}"
                )
            except Exception as e:
                logger.error(
                    f"发送激活邮件失败: {str(e)}, 用户: {new_user.username}, 邮箱: {user_email}"
                )
                
                new_user.delete()

                is_api_request = (
                    request.headers.get("X-Requested-With") == "XMLHttpRequest"
                    or request.content_type == "application/json"
                )

                if is_api_request:
                    return JsonResponse(
                        {
                            "success": False,
                            "error": f"邮件发送失败，请稍后重试。错误信息: {str(e)}",
                        },
                        status=500,
                    )
                else:
                    return render(
                        request,
                        "error.html",
                        context={
                            "error": f"邮件发送失败，请稍后重试。错误信息: {str(e)}"
                        },
                    )

            
            domain = ""
            is_limited_domain = False
            if user_email:
                domain = user_email.split("@")[-1].lower()
                
                limited_auth_domains = [
                    "126.com",
                    "163.com",
                    "qq.com",
                    "gmail.com",
                    "outlook.com",
                ]
                is_limited_domain = domain in limited_auth_domains

            
            is_api_request = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.content_type == "application/json"
            )

            if is_api_request:
                
                if is_limited_domain:
                    permission_message = f"您的邮箱域名（{domain}）权限受限，激活后可以下载数据库但不能提交自动计算任务。使用教育（*.edu.*）、军事（*.mil.*）或政府（*.gov.*）域名可获得完全访问权限。"
                else:
                    permission_message = "激活后您将拥有全部功能的访问权限。"

                return JsonResponse(
                    {
                        "success": True,
                        "message": f"注册成功！激活邮件已发送到 {user_email}，请查收邮件并点击激活链接。{permission_message}",
                        "email": user_email,
                        "requires_activation": True,
                        "limited_access": is_limited_domain,
                    }
                )
            else:
                
                return render(
                    request,
                    "register_success.html",
                    context={
                        "email": user_email,
                        "username": new_user.username,
                        "is_limited_domain": is_limited_domain,
                        "domain": domain,
                    },
                )
        else:
            
            
            is_api_request = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.content_type == "application/json"
            )

            if is_api_request:
                
                formatted_errors = {}
                for field, field_errors in error.items():
                    formatted_errors[field] = [str(err) for err in field_errors]

                return JsonResponse(
                    {"success": False, "errors": formatted_errors}, status=400
                )
            else:
                
                return render(request, "error.html", context={"error": error})
    
    elif request.method == "GET":
        
        user_register_form = UserRegisterForm()
        
        context = {"form": user_register_form}
        return render(request, "register.html", context)
    else:
        return HttpResponse("请使用GET或者POST请求")


import threading



def send_email_in_background(subject, message, from_email, recipient_list):
    send_mail(subject, message, from_email, recipient_list)


def send_test_email(request):
    subject = "Test Email from Django"
    message = "This is a test email sent from your Django application."
    from_email = "user@example.com"
    
    recipient_list = ["user@example.com"]

    
    email_thread = threading.Thread(
        target=send_email_in_background,
        args=(subject, message, from_email, recipient_list),
    )
    email_thread.start()

    
    return HttpResponse("Test email is being sent in the background.")


from django.core.mail import EmailMessage, get_connection
import hashlib
import time
from django.utils import timezone
from .models import Captcha




def password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")
        new_password = request.POST.get("new_password")
        code = request.POST.get("code")
        use_alternate_email = request.POST.get("use_alternate_email")
        context = {}

        
        users = User.objects.filter(email=email)
        user_count = users.count()

        if user_count == 0:
            context["error"] = "该邮箱不存在。"
            return render(request, "password_reset.html", context)
        elif user_count > 1:
            logger.info("Found more than one user with the same email.")
            context["error"] = "找到同一邮箱下的多个用户，请联系管理员。"
            return render(request, "password_reset.html", context)
        else:
            user = users.first()
        
        username = user.username

        if "send_code" in request.POST:
            
            code_str = "".join(random.choices(string.digits, k=6))

            
            timestamp = str(time.time())
            hash_object = hashlib.sha256(timestamp.encode("utf-8"))
            
            encrypt_id = hash_object.hexdigest()

            
            expire_time = timezone.now() + timezone.timedelta(minutes=10)

            
            captcha = Captcha.objects.create(
                code=code_str, expire_time=expire_time, encrypt_id=encrypt_id
            )

            
            request.session["encrypt_id"] = encrypt_id
            
            request.session["new_password"] = new_password

            logger.info(
                f"Send reset code to {email}: {code_str}, with new password {new_password}"
            )

            
            if use_alternate_email == "yes":
                
                connection = get_connection(
                    host="smtp.qq.com",
                    port=465,
                    username="user@example.com",
                    password="<CHANGE_ME_SMTP_PASSWORD>",
                    use_ssl=True,
                    use_tls=False,  
                )
                from_email = "user@example.com"
            else:
                
                connection = get_connection(
                    host="smtp.gmail.com",
                    port=587,
                    username="user@example.com",
                    password="your_default_app_password",
                    use_tls=True,
                    use_ssl=False,  
                )
                from_email = "user@example.com"

            
            email_message = EmailMessage(
                "您的密码重置验证码-CEMP",  
                f"您好，{username}，您的密码重置验证码是：{code_str}，该验证码将在5分钟后过期。",  
                from_email,  
                [email],  
                connection=connection,
            )

            try:
                email_message.send(fail_silently=False)
                
                context["email"] = email
                context["new_password"] = new_password
                context["message"] = (
                    f"您的用户名是：{username},验证码已发送到您的邮箱。"
                )
                context["show_code_input"] = True
                return render(request, "password_reset.html", context)
            except Exception as e:
                
                logger.error(f"Failed to send email to {email}: {str(e)}")
                context["error"] = "邮件发送失败，请稍后再试。"
                return render(request, "password_reset.html", context)

        elif "reset_password" in request.POST:
            
            encrypt_id = request.session.get("encrypt_id")

            if not encrypt_id:
                context["error"] = "会话已过期，请重新请求验证码。"
                return render(request, "password_reset.html", context)

            
            try:
                captcha = Captcha.objects.get(encrypt_id=encrypt_id)
            except Captcha.DoesNotExist:
                context["error"] = "验证码无效或已过期。"
                return render(request, "password_reset.html", context)

            
            if timezone.now() > captcha.expire_time:
                context["error"] = "验证码已过期，请重新请求验证码。"
                captcha.delete()  
                return render(request, "password_reset.html", context)

            if code == captcha.code and email == request.POST.get("email"):
                
                user.set_password(request.session.get("new_password"))
                user.save()
                
                del request.session["encrypt_id"]
                del request.session["new_password"]
                
                captcha.delete()
                return redirect("register:login")  
            else:
                context["error"] = "验证码无效或邮箱不匹配。"
                context["email"] = email
                context["new_password"] = new_password
                context["show_code_input"] = True
                return render(request, "password_reset.html", context)
    else:
        return render(request, "password_reset.html")





@login_required(login_url="/register/login/")
def user_delete(request, id):
    if request.method == "POST":
        user = User.objects.get(id=id)
        
        if request.user == user:
            
            logout(request)
            
            user.delete()
            return redirect("home:homepage")
        else:
            return HttpResponse("你没有删除操作的权限。")
    else:
        return HttpResponse("仅接受post请求。")


@login_required(login_url="/register/login/")
def profile_edit(request, id):
    user = User.objects.get(id=id)

    
    
    profile = Profile.objects.get(user_id=id)

    if request.method == "POST":
        
        if request.user != user:
            return HttpResponse("你没有权限修改此用户信息。")
        profile_form = ProfileForm(
            data=request.POST, files=request.FILES, instance=profile
        )
        if profile_form.is_valid():
            
            profile_cd = profile_form.cleaned_data
            
            profile.phone = profile_cd["phone"]
            profile.bio = profile_cd["bio"]

            
            if "avatar" in request.FILES:
                
                profile.avatar = profile_cd["avatar"]
            profile.save()
            
            return redirect("home:homepage")
        else:
            return HttpResponse("注册表单输入有误，请重新输入~")
    elif request.method == "GET":
        profile_form = ProfileForm()
        print(profile.avatar if profile.avatar else "No picture")
        context = {"profile": profile, "user": user}
        return render(request, "userprofile/edit.html", context)
    else:
        return HttpResponse("请使用GET或者POST请求")


@login_required(login_url="/register/login/")
def modify_email(request):
    from django.http import JsonResponse
    from .forms import validate_email_domain

    if request.method == "POST":
        form = EmailModifyForm(user=request.user, data=request.POST)
        if form.is_valid():
            new_email = form.cleaned_data["new_email"]
            request.user.email = new_email
            request.user.save()

            
            domain = new_email.split("@")[-1].lower()
            limited_auth_domains = [
                "126.com",
                "163.com",
                "qq.com",
                "gmail.com",
                "outlook.com",
            ]
            is_limited_domain = domain in limited_auth_domains

            if is_limited_domain:
                message = f"Email successfully changed to {new_email}. Warning: Your email domain ({domain}) has limited authorization. You can download database but cannot submit autocompute tasks. Use educational (*.edu.*), military (*.mil.*), or government (*.gov.*) domains for full access."
            else:
                message = f"Email successfully changed to {new_email}. You have full access to all features."

            return JsonResponse(
                {
                    "success": True,
                    "message": message,
                    "new_email": new_email,
                    "limited_access": is_limited_domain,
                }
            )
        else:
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(error) for error in field_errors]
            return JsonResponse({"success": False, "errors": errors})
    else:
        return JsonResponse(
            {"success": False, "message": "Only POST requests are supported"}
        )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_user_info(request):
    user = request.user

    
    try:
        profile = user.profile
        profile_data = {
            "phone": profile.phone,
            "bio": profile.bio,
            "avatar": request.build_absolute_uri(profile.avatar.url)
            if profile.avatar
            else None,
        }
    except:
        profile_data = {}

    
    try:
        from .models import UserProfile

        user_profile = UserProfile.objects.get(user=user)
        permissions = {
            "auto_compute_permission": user_profile.auto_compute_permission,
            "database_permission": user_profile.database_permission,
            "ml_prediction_permission": user_profile.ml_prediction_permission,
            "gaussian_permission": user_profile.gaussian_permission,
            "daily_task_limit": user_profile.daily_task_limit,
        }
    except:
        permissions = {}

    return Response(
        {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile": profile_data,
                "permissions": permissions,
            },
        }
    )


from rest_framework.authtoken.models import Token


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_or_create_token(request):
    user = request.user

    
    token, created = Token.objects.get_or_create(user=user)

    
    try:
        from .models import UserProfile

        user_profile = UserProfile.objects.get(user=user)
        permissions = {
            "auto_compute_permission": user_profile.auto_compute_permission,
            "database_permission": user_profile.database_permission,
            "ml_prediction_permission": user_profile.ml_prediction_permission,
            "gaussian_permission": user_profile.gaussian_permission,
            "daily_task_limit": user_profile.daily_task_limit,
        }
    except UserProfile.DoesNotExist:
        permissions = {}

    logger.info(
        f"Token {'created' if created else 'retrieved'} for user: {user.username} (Session → Token)"
    )

    return Response(
        {
            "success": True,
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "permissions": permissions,
            },
        }
    )


def user_activate(request):
    from django.http import JsonResponse
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.contrib.auth import get_user_model
    from .tokens import activation_token

    
    uidb64 = request.GET.get("uid")
    token = request.GET.get("token")

    
    is_api_request = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.content_type == "application/json"
        or "application/json" in request.headers.get("Accept", "")
    )

    
    if not uidb64 or not token:
        if is_api_request:
            return JsonResponse(
                {"success": False, "error": "无效的激活链接：缺少必要参数"}, status=400
            )
        else:
            return render(
                request,
                "activation_failed.html",
                context={
                    "error": "无效的激活链接：缺少必要参数",
                    "reason": "missing_params",
                },
            )

    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist) as e:
        logger.error(f"激活链接解析失败: {str(e)}, uidb64: {uidb64}")
        if is_api_request:
            return JsonResponse(
                {"success": False, "error": "无效的激活链接：用户不存在"}, status=400
            )
        else:
            return render(
                request,
                "activation_failed.html",
                context={
                    "error": "无效的激活链接：用户不存在",
                    "reason": "invalid_user",
                },
            )

    
    if user.is_active:
        logger.info(f"用户 {user.username} 已经激活，尝试重复激活")
        if is_api_request:
            return JsonResponse(
                {
                    "success": True,
                    "message": "您的账号已经激活，可以直接登录",
                    "already_active": True,
                }
            )
        else:
            return render(
                request,
                "activation_success.html",
                context={
                    "username": user.username,
                    "email": user.email,
                    "already_active": True,
                },
            )

    
    if activation_token.check_token(user, token):
        
        user.is_active = True
        user.save()

        logger.info(f"用户激活成功: {user.username} ({user.email})")

        if is_api_request:
            
            from rest_framework.authtoken.models import Token

            auth_token, created = Token.objects.get_or_create(user=user)

            return JsonResponse(
                {
                    "success": True,
                    "message": "账号激活成功！您现在可以登录了。",
                    "token": auth_token.key,  
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                }
            )
        else:
            
            return render(
                request,
                "activation_success.html",
                context={
                    "username": user.username,
                    "email": user.email,
                    "already_active": False,
                },
            )
    else:
        
        logger.warning(
            f"激活token无效或已过期: 用户 {user.username}, token: {token[:10]}..."
        )
        if is_api_request:
            return JsonResponse(
                {
                    "success": False,
                    "error": "激活链接无效或已过期（链接有效期为3天）",
                    "expired": True,
                },
                status=400,
            )
        else:
            return render(
                request,
                "activation_failed.html",
                context={
                    "error": "激活链接无效或已过期",
                    "reason": "expired_token",
                    "username": user.username,
                    "email": user.email,
                },
            )


@csrf_exempt
def resend_activation_email(request):
    from django.http import JsonResponse
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes
    from django.core.mail import EmailMessage, get_connection
    from django.conf import settings
    from .tokens import activation_token

    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if request.content_type == "application/json":
        try:
            body = (
                request.body.decode("utf-8")
                if isinstance(request.body, bytes)
                else request.body
            )
            json_data = json.loads(body)
            email = json_data.get("email", "")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    else:
        email = request.POST.get("email", "")

    if not email:
        return JsonResponse({"success": False, "error": "请提供邮箱地址"}, status=400)

    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        return JsonResponse(
            {"success": False, "error": "未找到该邮箱对应的未激活账号"}, status=404
        )

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = activation_token.make_token(user)
    activation_link = (
        f"{settings.SITE_DOMAIN}/register/activate?uid={uidb64}&token={token}"
    )

    subject = "激活您的CEMP账号 - Activate Your CEMP Account"
    message = f"""
您好 {user.username}，

这是您重新请求的激活邮件。

请点击下面的链接激活您的账号：
{activation_link}

此链接将在3天后过期。

如果您没有注册CEMP账号，请忽略此邮件。

---
Hello {user.username},

This is your re-requested activation email.

Please click the link below to activate your account:
{activation_link}

This link will expire in 3 days.

If you did not register for a CEMP account, please ignore this email.

CEMP Team
"""

    try:
        connection = get_connection(
            host="smtp.qq.com",
            port=465,
            username="user@example.com",
            password="<CHANGE_ME_SMTP_PASSWORD>",
            use_ssl=True,
            use_tls=False,
        )
        email_message = EmailMessage(
            subject,
            message,
            "user@example.com",
            [email],
            connection=connection,
        )
        email_message.send(fail_silently=False)
        logger.info(f"重新发送激活邮件到: {email}, 用户: {user.username}")
    except Exception as e:
        logger.error(f"重新发送激活邮件失败: {str(e)}, 用户: {user.username}")
        return JsonResponse(
            {"success": False, "error": f"邮件发送失败，请稍后重试: {str(e)}"},
            status=500,
        )

    is_api_request = (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.content_type == "application/json"
    )

    if is_api_request:
        return JsonResponse(
            {"success": True, "message": f"激活邮件已重新发送到 {email}，请查收。"}
        )
    else:
        return render(
            request,
            "activation_resent.html",
            context={"email": email, "username": user.username},
        )
