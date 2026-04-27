from phe import paillier # 开源库
import random # 选择随机数
from Crypto.Cipher import AES

##################### 设置参数
# 服务器端保存的数值
BLOCK_SIZE = 16

def _new_aes_cipher(k, pos):
    # 用查询位置pos生成nonce，使每个位置使用不同的AES-CTR密钥流
    nonce = pos.to_bytes(8, byteorder='big')
    return AES.new(k, AES.MODE_CTR, nonce=nonce)

def symmetric_encrypt(k, pos, message):
    # 将整数明文固定为16字节，再用AES加密成密文整数，便于服务器计算
    message_bytes = int(message).to_bytes(BLOCK_SIZE, byteorder='big')
    cipher_bytes = _new_aes_cipher(k, pos).encrypt(message_bytes)
    return int.from_bytes(cipher_bytes, byteorder='big')

def symmetric_decrypt(k, pos, cipher):
    # 客户端取回指定位置的密文整数后，用同一个密钥k和pos解密得到明文
    cipher_bytes = int(cipher).to_bytes(BLOCK_SIZE, byteorder='big')
    message_bytes = _new_aes_cipher(k, pos).decrypt(cipher_bytes)
    return int.from_bytes(message_bytes, byteorder='big')

plain_message_list = [100,200,300,400,500,600,700,800,900,1000]
# 客户端保存AES密钥k；服务器只保存下面生成的AES密文列表
k = b'lab1-symmetric-k'
message_list = [symmetric_encrypt(k, i, m) for i, m in enumerate(plain_message_list)]
length = len(message_list)
# 客户端生成公私钥
public_key, private_key = paillier.generate_paillier_keypair()
# 客户端随机选择一个要读的位置
pos = random.randint(0,length-1)
print("要读起的数值位置为：",pos)

##################### 客户端生成密文选择向量
select_list=[]
enc_list=[]
for i in range(length):
    select_list.append(  i == pos )
    enc_list.append( public_key.encrypt(select_list[i]) )

# for element in select_list:
#     print(element)
# for element in enc_list:
#     print(private_key.decrypt(element))

##################### 服务器端进行运算
c=0
for i in range(length):
    c = c + message_list[i] * enc_list[i]
print("产生密文：",c.ciphertext())

##################### 客户端进行解密 
selected_cipher=private_key.decrypt(c)
print("selected ciphertext:",selected_cipher)
# Paillier只负责隐私取回AES密文，真正的明文还要再经过AES解密
m=symmetric_decrypt(k, pos, selected_cipher)
print("得到数值：",m)
