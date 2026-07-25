import requests
import logging
from decimal import Decimal
from django.conf import settings
from apps.payments.gateways.base import PaymentGateway
from apps.payments.exceptions import (
    PaymentGatewayUnavailable,
    PaymentValidationFailed,
    PaymentInitializationFailed,
    PaymentRefundFailed
)

logger = logging.getLogger(__name__)

class SSLCommerzGateway(PaymentGateway):
    def __init__(self):
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_pass = settings.SSLCOMMERZ_STORE_PASSWORD
        self.is_sandbox = getattr(settings, 'SSLCOMMERZ_SANDBOX', True)
        
        if self.is_sandbox:
            self.base_url = "https://sandbox.sslcommerz.com"
        else:
            self.base_url = "https://securepay.sslcommerz.com"
            
        self.timeout = (5.0, 15.0)  # (connect_timeout, read_timeout)

    def initialize_payment(self, payment_id: str, amount: Decimal, currency: str, customer_info: dict, return_url_base: str) -> str:
        url = f"{self.base_url}/gwprocess/v4/api.php"
        
        payload = {
            'store_id': self.store_id,
            'store_passwd': self.store_pass,
            'total_amount': str(amount),
            'currency': currency,
            'tran_id': payment_id,
            'success_url': f"{return_url_base}/api/payments/sslcommerz/success/",
            'fail_url': f"{return_url_base}/api/payments/sslcommerz/fail/",
            'cancel_url': f"{return_url_base}/api/payments/sslcommerz/cancel/",
            'ipn_url': f"{return_url_base}/api/payments/sslcommerz/ipn/",
            
            # Customer Info (Required by SSLCommerz)
            'cus_name': customer_info.get('name', 'N/A'),
            'cus_email': customer_info.get('email', 'N/A'),
            'cus_add1': customer_info.get('address', 'N/A'),
            'cus_city': customer_info.get('city', 'N/A'),
            'cus_postcode': customer_info.get('postcode', 'N/A'),
            'cus_country': customer_info.get('country', 'N/A'),
            'cus_phone': customer_info.get('phone', 'N/A'),
            'shipping_method': 'NO',
        }
        
        try:
            logger.info(f"SSLCommerz Init Request: tran_id={payment_id}")
            response = requests.post(url, data=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'SUCCESS':
                return data.get('GatewayPageURL')
            else:
                logger.error(f"SSLCommerz Init Failed: {data.get('failedreason')}")
                raise PaymentInitializationFailed(data.get('failedreason', 'Unknown error'))
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz connection error during init: {e}")
            raise PaymentGatewayUnavailable("Failed to connect to SSLCommerz") from e

    def validate_payment(self, payload: dict) -> dict:
        """
        Validates the callback using SSLCommerz Validation API.
        """
        val_id = payload.get('val_id')
        if not val_id:
            raise PaymentValidationFailed("Missing val_id in payload")
            
        url = f"{self.base_url}/validator/api/validationserverAPI.php"
        params = {
            'val_id': val_id,
            'store_id': self.store_id,
            'store_passwd': self.store_pass,
            'v': 1,
            'format': 'json'
        }
        
        try:
            logger.info(f"SSLCommerz Validation Request: val_id={val_id}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            status = data.get('status')
            if status not in ['VALID', 'VALIDATED']:
                logger.error(f"SSLCommerz Validation Failed: status={status}")
                raise PaymentValidationFailed(f"Transaction validation failed with status {status}")
                
            return {
                'valid': True,
                'amount': Decimal(data.get('amount', '0.00')),
                'currency': data.get('currency'),
                'tran_id': data.get('tran_id'),
                'raw_metadata': {
                    'val_id': data.get('val_id'),
                    'bank_tran_id': data.get('bank_tran_id'),
                    'card_type': data.get('card_type'),
                    'card_no': data.get('card_no'),
                    'card_issuer': data.get('card_issuer'),
                    'store_amount': data.get('store_amount'),
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz connection error during validation: {e}")
            raise PaymentGatewayUnavailable("Failed to connect to SSLCommerz validation API") from e

    def refund_payment(self, refund_id: str, payment_id: str, amount: Decimal, bank_tran_id: str = None) -> dict:
        if not bank_tran_id:
            raise PaymentRefundFailed("bank_tran_id is required for SSLCommerz refund")
            
        url = f"{self.base_url}/validator/api/merchantTransIDvalidationAPI.php"
        params = {
            'refund_amount': str(amount),
            'refund_remarks': f"Refund for {payment_id}",
            'bank_tran_id': bank_tran_id,
            'refe_id': refund_id,
            'store_id': self.store_id,
            'store_passwd': self.store_pass,
            'format': 'json'
        }
        
        try:
            logger.info(f"SSLCommerz Refund Request: bank_tran_id={bank_tran_id}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            status = data.get('status')
            if status == 'success':
                return {
                    'success': True,
                    'raw_metadata': {
                        'refund_ref_id': data.get('refund_ref_id'),
                        'errorReason': data.get('errorReason')
                    }
                }
            else:
                error = data.get('errorReason', 'Unknown error')
                logger.error(f"SSLCommerz Refund Failed: {error}")
                raise PaymentRefundFailed(f"Gateway refund failed: {error}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SSLCommerz connection error during refund: {e}")
            raise PaymentGatewayUnavailable("Failed to connect to SSLCommerz refund API") from e
