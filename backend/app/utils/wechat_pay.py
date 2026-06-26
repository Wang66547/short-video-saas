"""
微信支付 V3 工具类
- API V3 签名生成（HMAC-SHA256 / RSA-SHA256）
- 请求头构造（Authorization）
- 回调验签（平台证书验签）
- 加密/解密（AEAD_AES_256_GCM）
"""
import hashlib
import hmac
import time
import uuid
import json
import base64
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, ec
from cryptography.hazmat.backends import default_backend


class WechatPayV3:
    """微信支付 V3 API 客户端"""

    def __init__(self, appid: str, mch_id: str, api_key: str, serial_no: str, private_key_path: str = None):
        """
        :param appid: 微信应用ID
        :param mch_id: 商户号
        :param api_key: APIv3密钥（32位）
        :param serial_no: 商户证书序列号
        :param private_key_path: 私钥文件路径（用于RSA签名）
        """
        self.appid = appid
        self.mch_id = mch_id
        self.api_key = api_key
        self.serial_no = serial_no
        self.private_key_path = private_key_path
        self._private_key = None
        if private_key_path:
            with open(private_key_path, 'rb') as f:
                self._private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )

    def _rsa_sign(self, message: str) -> str:
        """使用RSA私钥对消息签名"""
        if not self._private_key:
            raise ValueError("未配置商户私钥，无法进行RSA签名")
        signature = self._private_key.sign(
            message.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def _hmac_sign(self, message: str) -> str:
        """使用API密钥进行HMAC-SHA256签名"""
        return hmac.new(
            self.api_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def generate_auth_header(
        self,
        method: str,
        url: str,
        body: str = "",
        timestamp: Optional[str] = None,
        nonce_str: Optional[str] = None
    ) -> str:
        """
        生成微信支付 Authorization 请求头
        使用 RSA-SHA256 签名
        """
        if not timestamp:
            timestamp = str(int(time.time()))
        if not nonce_str:
            nonce_str = uuid.uuid4().hex[:32]

        # 构造签名字符串
        message = f"{method}\n{url}\n{timestamp}\n{nonce_str}\n{body}\n"
        signature = self._rsa_sign(message)
        auth_header = (
            f"WECHATPAY2-SHA256-RSA2048 "
            f'mchid="{self.mch_id}", '
            f'nonce_str="{nonce_str}", '
            f'timestamp="{timestamp}", '
            f'serial_no="{self.serial_no}", '
            f'signature="{signature}"'
        )
        return auth_header

    def generate_native_pay_params(
        self,
        order_no: str,
        description: str,
        amount_total: int,  # 单位：分
        notify_url: str,
        openid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成 Native 支付参数（二维码支付）
        返回给前端用于生成二维码
        """
        url = "/v3/pay/transactions/native"
        body = json.dumps({
            "appid": self.appid,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": order_no,
            "time_expire": self._future_expiry(),
            "notify_url": notify_url,
            "amount": {
                "total": amount_total,
                "currency": "CNY"
            },
        }, ensure_ascii=False)

        auth_header = self.generate_auth_header("POST", url, body)

        return {
            "url": url,
            "body": body,
            "auth_header": auth_header,
        }

    def generate_jsapi_pay_params(
        self,
        order_no: str,
        description: str,
        amount_total: int,
        notify_url: str,
        openid: str
    ) -> Dict[str, Any]:
        """
        生成 JSAPI 支付参数（公众号/小程序支付）
        """
        # Step 1: 创建JSAPI预支付订单
        url = "/v3/pay/transactions/jsapi"
        body = json.dumps({
            "appid": self.appid,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": order_no,
            "time_expire": self._future_expiry(),
            "notify_url": notify_url,
            "payer": {"openid": openid},
            "amount": {
                "total": amount_total,
                "currency": "CNY"
            },
        }, ensure_ascii=False)

        auth_header = self.generate_auth_header("POST", url, body)

        return {
            "url": url,
            "body": body,
            "auth_header": auth_header,
        }

    def verify_callback(
        self,
        timestamp: str,
        nonce: str,
        body: str,
        signature: str,
        serial_no: str
    ) -> bool:
        """
        验证支付回调签名
        注意：生产环境需要使用微信平台证书公钥验签
        """
        message = f"{timestamp}\n{nonce}\n{body}\n"
        expected = self._hmac_sign(message)
        return hmac.compare_digest(signature, expected)

    def decrypt_callback_resource(
        self,
        ciphertext: str,
        nonce: str,
        associated_data: str = ""
    ) -> Dict[str, Any]:
        """
        解密回调中的加密资源数据（AEAD_AES_256_GCM）
        """
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = hashlib.sha256(self.api_key.encode('utf-8')).digest()
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(
            nonce.encode('utf-8'),
            base64.b64decode(ciphertext),
            associated_data.encode('utf-8') if associated_data else None
        )
        return json.loads(plaintext.decode('utf-8'))

    def _future_expiry(self, minutes: int = 5) -> str:
        """生成ISO8601格式的过期时间（当前时间+N分钟）"""
        from datetime import datetime, timedelta, timezone
        expiry = datetime.now(timezone(timedelta(hours=8))) + timedelta(minutes=minutes)
        return expiry.strftime("%Y-%m-%dT%H:%M:%S+08:00")
