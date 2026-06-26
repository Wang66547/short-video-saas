"""
支付宝工具类
- RSA2 签名与验签
- 订单创建
- 回调验签
"""
import base64
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


class AlipayClient:
    """支付宝SDK客户端（RSA2签名版）"""

    def __init__(self, app_id: str, private_key: str, alipay_public_key: str, gateway: str = "https://openapi.alipay.com/gateway.do"):
        """
        :param app_id: 支付宝应用ID
        :param private_key: 应用私钥（PEM格式字符串）
        :param alipay_public_key: 支付宝公钥（PEM格式字符串）
        :param gateway: 支付宝网关地址
        """
        self.app_id = app_id
        self.gateway = gateway
        # 加载私钥
        self.private_key = serialization.load_pem_private_key(
            private_key.encode('utf-8'),
            password=None,
            backend=None
        )
        # 加载支付宝公钥
        self.alipay_public_key = serialization.load_pem_public_key(
            alipay_public_key.encode('utf-8'),
            backend=None
        )

    def sign(self, params: dict) -> str:
        """
        使用RSA2(SHA256WithRSA)对参数签名
        """
        # 1. 排除sign和sign_type，按字母排序
        sorted_params = sorted(
            [(k, v) for k, v in params.items() if k != 'sign' and k != 'sign_type' and v is not None]
        )
        # 2. 拼接成 key1=value1&key2=value2...
        sign_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        # 3. RSA2签名
        signature = self.private_key.sign(
            sign_string.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def verify(self, params: dict, sign: str) -> bool:
        """
        验证支付宝回调签名
        """
        # 1. 排除sign和sign_type
        sorted_params = sorted(
            [(k, v) for k, v in params.items() if k != 'sign' and k != 'sign_type']
        )
        sign_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        # 2. RSA2验签
        try:
            signature_bytes = base64.b64decode(sign)
            self.alipay_public_key.verify(
                signature_bytes,
                sign_string.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

    def create_page_pay_url(
        self,
        order_no: str,
        total_amount: str,
        subject: str,
        notify_url: str
    ) -> str:
        """
        生成支付宝电脑网站/手机网站支付URL
        前端直接跳转到该URL即可完成支付
        """
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.page.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": notify_url,
            "return_url": "about:blank",
            "biz_content": json.dumps({
                "out_trade_no": order_no,
                "total_amount": total_amount,
                "subject": subject,
                "product_code": "FAST_INSTANT_TRADE_PAY",
            }, ensure_ascii=False),
        }
        params["sign"] = self.sign(params)
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.gateway}?{query_string}"

    def create_wap_pay_url(
        self,
        order_no: str,
        total_amount: str,
        subject: str,
        notify_url: str
    ) -> str:
        """
        生成支付宝WAP支付URL（手机网站支付）
        """
        params = {
            "app_id": self.app_id,
            "method": "alipay.trade.wap.pay",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": notify_url,
            "biz_content": json.dumps({
                "out_trade_no": order_no,
                "total_amount": total_amount,
                "subject": subject,
                "product_code": "QUICK_WAP_WAY",
            }, ensure_ascii=False),
        }
        params["sign"] = self.sign(params)
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.gateway}?{query_string}"
