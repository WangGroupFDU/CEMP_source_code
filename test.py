import hashlib
import time


def main():
    """
    功能目的：手动生成一个基于时间戳的 SHA256 示例字符串。
    输入参数：无。
    返回值：无，直接打印哈希字符串和长度。
    关键流程：读取当前时间戳，编码后计算 SHA256。
    边界情况：该文件名称会被 unittest 发现，因此逻辑必须放在 main guard 下。
    """
    timestamp = str(time.time())

    hash_object = hashlib.sha256(timestamp.encode('utf-8'))

    encrypt_id = hash_object.hexdigest()

    print(encrypt_id)
    print(len(encrypt_id))


if __name__ == '__main__':
    main()
