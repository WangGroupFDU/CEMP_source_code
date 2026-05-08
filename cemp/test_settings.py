from .settings import *  



ROOT_URLCONF = "cemp.test_urls"


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
TICKETS_EMAIL_ASYNC = False
TICKETS_ENABLE_EMAIL_NOTIFICATIONS = False


ALLOWED_HOSTS = ["testserver", "127.0.0.1", "localhost"]


DATABASES = {
    "default": {
        **DATABASES["default"],  
        "NAME": "/tmp/cemp_ticket_test.sqlite3",
    },
}
DATABASE_ROUTERS = []
