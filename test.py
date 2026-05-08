import hashlib
import time


timestamp = str(time.time())


hash_object = hashlib.sha256(timestamp.encode('utf-8'))


encrypt_id = hash_object.hexdigest()

print(encrypt_id)
print(len(encrypt_id))
