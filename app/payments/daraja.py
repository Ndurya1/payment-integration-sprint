import httpx
import os, base64
from datetime import datetime, timezone, timedelta
from app.config import settings

BASE= "https://sandbox.safaricom.co.ke"
EAT= timezone(timedelta(hours=3))


class DarajaClient:
    async def get_access_token(self) -> str:
        consumer_key = settings.daraja_consumer_key
        consumer_secret = settings.daraja_consumer_secret
        auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

        res = httpx.get(
            f"{BASE}/oauth/v1/generate",
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"},
            timeout=10,
        )
        res.raise_for_status()
        return res.json()["access_token"]

    def mpesa_timestamp(self)-> str:
        return datetime.now(EAT).strftime("%Y%m%d%H%M%S")

    def daraja_password(self)->str:
        return base64.b64encode(
                (settings.daraja_shortcode + settings.daraja_passkey + await self.mpesa_timestamp()).encode()
                ).decode()

    async def send_stk_push(self, phone_number:str, amount: int, account_reference: str, transaction_desc: str) -> str:
        token = await self.get_access_token()
        timestamp = self.mpesa_timestamp()
        shortcode = settings.daraja_shortcode
        password =self.daraja_password()
        res = httpx.post(
            f"{BASE}/mpesa/stkpush/v1/processrequest",
            headers={"Authorization": f"Bearer {token}"},
            json={
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,               # whole numbers, no cents
            "PartyA": phone_number,                # 2547XXXXXXXX format. no leading + or 0.
            "PartyB": shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.daraja_callback_url,
            "AccountReference": account_reference,  # not more that 12 characters long
            "TransactionDesc": transaction_desc,
            },
            timeout=15,
        )
        data = res.json()
        return data

    async def stk_query(self, checkout_request_id: str):
        token = await self.get_access_token()
        timestamp = await self.mpesa_timestamp()
        password= await self.daraja_password()
        shortcode = settings.daraja_shortcode

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        # print(payload)

        async with httpx.AsyncClient() as client:
            response =  client.post(
                f"{BASE}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers=headers
            )

        return response.json()
    
    

