import os


def main():
    """
    功能目的：手动检查 ionic_liquid 测试数据目录路径。
    输入参数：无。
    返回值：无，直接向终端打印路径检查结果。
    关键流程：根据 views.py 的位置推导测试目录，并报告目录是否存在。
    边界情况：该脚本不能在 import 阶段执行，否则会干扰 Django 测试发现。
    """
    views_path = os.path.dirname(os.path.abspath('ionic_liquid/views.py'))
    test_box_path = os.path.join(views_path, 'ionic_liquid', 'test_box', 'query_similar_IL')
    print('Views path:', views_path)
    print('Test box path:', test_box_path)
    print('Test box exists:', os.path.exists(test_box_path))
    print('Files:', os.listdir(test_box_path) if os.path.exists(test_box_path) else 'N/A')


if __name__ == '__main__':
    main()
