
from django.conf import settings


class MyRouter:
    """
    控制 crystals 应用的数据库路由。

    生产环境可通过 CEMP_ENABLE_MYSQL=true 配置独立 MySQL；公开 demo 默认只有
    SQLite，因此需要自动回落到 default，避免本地安装和测试被不存在的 mysql 连接阻断。
    """
    route_app_labels = {'crystals'}

    def _database_alias(self):
        """
        功能目的：返回 crystals 应用当前应使用的数据库别名。
        输入参数：无，直接读取 Django settings.DATABASES。
        返回值：配置了 mysql 时返回 'mysql'，否则返回 'default'。
        关键流程：只判断数据库别名是否存在，不主动创建连接。
        边界情况：公开版未启用 MySQL 时，所有 crystals 表随 SQLite demo 库迁移。
        """
        if 'mysql' in settings.DATABASES:
            return 'mysql'
        return 'default'

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self._database_alias()
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return self._database_alias()
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == self._database_alias()
        return None
