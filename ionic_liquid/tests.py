import json

from django.test import TestCase

from ionic_liquid.models import IL
from ionic_liquid.views import _IL_FINGERPRINT_CACHE


class IonicLiquidSimilarityApiTests(TestCase):
    """验证相似性 API 能直接使用公开数据库，而不依赖未发布的指纹文件。"""

    def setUp(self):
        """
        功能目的：为每个测试建立一条最小公开离子液体 QC 记录。
        输入参数：无。
        返回值：无。
        关键流程：写入所有非空模型字段，并清除进程级指纹缓存。
        可能报错或边界情况：字段契约变化时测试会直接失败并提示迁移不一致。
        """
        _IL_FINGERPRINT_CACHE.clear()
        IL.objects.create(
            Name="ethylammonium acetate",
            SMILES="CC(=O)[O-].CC[NH3+]",
            Energy_Hatree=-321.123,
            Thermal_correction_to_Gibbs_Free_Energy_Hatree=-0.045,
            Thermal_correction_to_Enthalpy_Hatree=-0.032,
            Entropy_J_per_mol_K=125.4,
            HOMO_Hatree=-0.201,
            LUMO_Hatree=-0.035,
            Dipole_Debye=7.2,
            Gibbs_Free_Energy_Hatree=-321.168,
            Enthalpy_Hatree=-321.155,
            ECW_V=4.12,
            Software="ORCA",
            Theory_Level="public test",
            Source="QC demo",
        )

    def tearDown(self):
        """
        功能目的：清除测试生成的进程级缓存，避免测试顺序影响结果。
        输入参数：无。
        返回值：无。
        关键流程：仅清空内存缓存，数据库由 Django 测试事务回滚。
        可能报错或边界情况：无。
        """
        _IL_FINGERPRINT_CACHE.clear()

    def test_similarity_search_uses_loaded_public_database(self):
        """
        功能目的：验证实验离子液体相似性查询可由公开 SQLite 数据完成。
        输入参数：无，使用测试客户端发送 JSON 请求。
        返回值：无，断言 HTTP 状态、命中结构和性质。
        关键流程：查询与库内相同的 SMILES，应得到 100% 相似度结果。
        可能报错或边界情况：指纹生成、URL 路由或字段映射错误都会触发断言失败。
        """
        response = self.client.post(
            "/ionic_liquid/api/similarity_search/",
            data=json.dumps(
                {
                    "smiles": "CC(=O)[O-].CC[NH3+]",
                    "mol_type": "il",
                    "source": "experiment",
                    "topk": 1,
                    "method": "tanimoto",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["results"][0]["similarity"], "100.00%")
        self.assertEqual(payload["results"][0]["properties"]["ECW (V)"], "4.12")


