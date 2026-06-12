from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

from register.models import Profile, UserProfile


class Command(BaseCommand):
    help = "Create or update the local CEMP demo user."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="cemp_demo")
        parser.add_argument("--password", default="cemp_demo_local")
        parser.add_argument("--email", default="cemp_demo@example.invalid")

    def handle(self, *args, **options):
        """
        功能目的：
            为公开版本地部署创建稳定 demo 账号和 API token。
        输入参数：
            --username、--password、--email。
        返回值：
            通过 stdout 输出账号名和 token。
        关键流程：
            创建或更新用户密码；补齐 Profile/UserProfile；开启数据库和 ML 预测权限。
        可能报错或边界情况：
            该账号只用于本地 demo 数据库，不应复用到公开生产服务。
        """
        user_model = get_user_model()
        user, _ = user_model.objects.get_or_create(
            username=options["username"],
            defaults={"email": options["email"], "is_active": True},
        )
        user.email = options["email"]
        user.is_active = True
        user.set_password(options["password"])
        user.save()

        Profile.objects.get_or_create(user=user)
        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        user_profile.database_permission = True
        user_profile.ml_prediction_permission = True
        user_profile.auto_compute_permission = False
        user_profile.gaussian_permission = False
        user_profile.daily_task_limit = 0
        user_profile.save()

        token, _ = Token.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(f"username: {user.username}"))
        self.stdout.write(self.style.SUCCESS(f"password: {options['password']}"))
        self.stdout.write(self.style.SUCCESS(f"token: {token.key}"))
