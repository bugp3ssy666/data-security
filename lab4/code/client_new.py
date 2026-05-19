import pymysql
import random
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

local_table = {}
key = get_random_bytes(16)
base_iv = get_random_bytes(16)

# 单列数据库连接配置
DB_CONFIG = dict(host='localhost', user='user1', passwd='123456', database='test_db')

# 重复插入实验组
TEST_REPEAT_VALUE = 'apple'
TEST_REPEAT_TIMES = 140
PRINT_EVERY = 1

# Node.h 定义 M = 128. 当叶子节点的行数达到 M 时会发生分裂
# 为观察分裂过程，设置 SPLIT_THRESHOLD = 128，插入时行数达到该值时打印当前状态
SPLIT_THRESHOLD = 128

# 让重复值总是插入到左边，观察分裂时重复值如何分布在新旧节点中
FORCE_LEFT_DUPLICATES = True

def AES_ENC(plaintext, iv):
    # AES加密
    aes = AES.new(key, AES.MODE_CBC, iv=iv)
    padded_data = pad(plaintext, AES.block_size, style='pkcs7')
    ciphertext = aes.encrypt(padded_data)
    return ciphertext

def AES_DEC(ciphertext, iv):
    # AES解密
    aes = AES.new(key, AES.MODE_CBC, iv=iv)
    padded_data = aes.decrypt(ciphertext)
    plaintext = unpad(padded_data, AES.block_size, style='pkcs7')
    return plaintext

def Random_Encrypt(plaintext):
    # 随机生成iv来保证加密结果的随机性
    iv = get_random_bytes(16)
    ciphertext = AES_ENC(iv + AES_ENC(plaintext.encode('utf-8'), iv), base_iv)
    ciphertext = base64.b64encode(ciphertext)
    return ciphertext.decode('utf-8')

def Random_Decrypt(ciphertext):
    plaintext = AES_DEC(base64.b64decode(ciphertext.encode('utf-8')), base_iv)
    plaintext = AES_DEC(plaintext[16:], plaintext[:16])
    return plaintext.decode('utf-8')

def CalPos(plaintext):
    # 插入plaintext，返回对应的pos
    presum = sum([v for k, v in local_table.items() if k < plaintext])
    if plaintext in local_table:
        local_table[plaintext] += 1
        # 强制重复值插入到左边
        if FORCE_LEFT_DUPLICATES:
            return presum
        return random.randint(presum, presum + local_table[plaintext] - 1)
    else:
        local_table[plaintext] = 1
        return presum

def GetLeftPos(plaintext):
    return sum([v for k, v in local_table.items() if k < plaintext])

def GetRightPos(plaintext):
    return sum([v for k, v in local_table.items() if k <= plaintext])

def Insert(plaintext):
    ciphertext = Random_Encrypt(plaintext)
    pos = CalPos(plaintext)
    # 连接数据库
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(f"call pro_insert({pos},'{ciphertext}')")
    conn.commit()
    conn.close()
    return pos, ciphertext

# 获取当前所有编码和对应的密文，按编码排序
def FetchEncodings():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("select encoding, ciphertext from example order by encoding, ciphertext")
    rows = cur.fetchall()
    conn.close()
    return [(int(encoding), ciphertext) for encoding, ciphertext in rows]

# 获取当前编码范围和示例密文，观察更新范围和示例变化
def FetchUpdateRange():
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("select FHStart(), FHEnd()")
    start_update, end_update = cur.fetchone()
    conn.close()
    return int(start_update), int(end_update)

def ShortCipher(ciphertext):
    return ciphertext[:12] + '...'

# 打印当前状态：插入的值、位置、行数、编码范围、部分编码列表，以及更新的编码数量和示例
def PrintEncodingState(step, pos, rows, previous):
    current = {ciphertext: encoding for encoding, ciphertext in rows}
    changed = [
        (ciphertext, previous[ciphertext], current[ciphertext])
        for ciphertext in previous
        if ciphertext in current and previous[ciphertext] != current[ciphertext]
    ]
    start_update, end_update = FetchUpdateRange()
    encodings = [encoding for encoding, _ in rows]
    preview = encodings[:8]
    if len(encodings) > 12:
        preview = encodings[:8] + ['...'] + encodings[-2:]

    print(f"\ninsert #{step:03d}: value={TEST_REPEAT_VALUE!r}, pos={pos}, rows={len(rows)}")
    print(f"  update range: [{start_update}, {end_update})")
    print(f"  ordered encodings: {preview}")
    if changed:
        print(f"  encoding updated for {len(changed)} existing row(s):")
        for ciphertext, old, new in changed[:2]:
            print(f"    {ShortCipher(ciphertext)} {old} -> {new}")
        if len(changed) > 2:
            print(f"    ... {len(changed) - 2} more")
    else:
        print("  encoding updated for 0 existing row(s)")

    if len(rows) == SPLIT_THRESHOLD:
        print(f"  leaf split point reached: rows == M == {SPLIT_THRESHOLD}")

    return current

def Search(left, right):
    # 搜索[left,right]中的信息
    left_pos = GetLeftPos(left)
    right_pos = GetRightPos(right)
    # 连接数据库
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        f"select ciphertext from example where encoding >= FHSearch({left_pos}) and encoding < FHSearch({right_pos})")
    rest = cur.fetchall()
    for x in rest:
        print(f"ciphertext: {x[0]} plaintext: {Random_Decrypt(x[0])}")

if __name__ == '__main__':
    previous = {}
    for step in range(1, TEST_REPEAT_TIMES + 1):
        # 插入重复值，获取其位置，并打印当前状态
        pos, _ = Insert(TEST_REPEAT_VALUE)
        rows = FetchEncodings()
        # 只有在特定步骤或达到分裂点时才打印状态
        should_print = (
            step <= 5
            or step % PRINT_EVERY == 0
            or step in (SPLIT_THRESHOLD - 1, SPLIT_THRESHOLD, SPLIT_THRESHOLD + 1)
        )
        if should_print:
            previous = PrintEncodingState(step, pos, rows, previous)
        else:
            previous = {ciphertext: encoding for encoding, ciphertext in rows}