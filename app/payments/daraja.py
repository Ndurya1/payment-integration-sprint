import httpx
import os, base64
from datetime import datetime, timezone, timedelta
from app.config import settings

BASE= "https://sandbox.safaricom.co.ke"
EAT= timezone(timedelta(hours=3))


class DarajaClient:
    async def get_access_token(self) -> str:
        print(">>> REQUESTING ACCESS TOKEN")
        print(">>> BASE:", repr(BASE))
        consumer_key = settings.daraja_consumer_key
        consumer_secret = settings.daraja_consumer_secret
        auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

        async with httpx.AsyncClient() as client:
         res =await client.get(
            f"{BASE}/oauth/v1/generate",
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"},
            timeout=10,
        )
        res.raise_for_status()

        print(">>> ACCESS TOKEN RECEIVED")

        return res.json()["access_token"]
        

    def mpesa_timestamp(self)-> str:
        return datetime.now(EAT).strftime("%Y%m%d%H%M%S")

    def daraja_password(self, timestamp: str) -> str:
        raw = (
        settings.daraja_shortcode
        + settings.daraja_passkey
        + timestamp
    )

        return base64.b64encode(raw.encode()).decode()

    async def send_stk_push(self, phone_number:str, amount: int, account_reference: str, transaction_desc: str) -> str:
        token = await self.get_access_token()
        timestamp = self.mpesa_timestamp()
        shortcode = settings.daraja_shortcode
        password =self.daraja_password(timestamp)

        print(">>> SENDING STK PUSH"),

        async with httpx.AsyncClient() as client:
         res =await client.post(
           
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
        timestamp = self.mpesa_timestamp()
        password=  self.daraja_password(timestamp)
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
            response = await client.post(
                f"{BASE}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers=headers
            )
        print("STATUS:", response.status_code)
        print("BODY:", response.text)
        return response.json()
    
    

