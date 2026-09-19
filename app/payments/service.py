# app/payments/servic
from app.payments.daraja import DarajaClient


class PaymentService:
    def __init__(self):
        self.daraja = DarajaClient()

    async def initiate_stk_payment(
        self,
        phone_number: str,
        amount: int,
        account_reference: str,
        transaction_desc: str,
    ):
       

        response = await self.daraja.send_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc,
        )

        # ResponseCode == 0 only means Safaricom accepted
        # the STK request for processing.
        if response.get("ResponseCode") != "0":
            return {
                "success": False,
                "message": "STK Push request was rejected",
                "data": response,
            }

        return {
            "success": True,
            "message": "STK Push sent successfully",
            "checkout_request_id": response.get("CheckoutRequestID"),
            "merchant_request_id": response.get("MerchantRequestID"),
        }

    async def query_stk_status(self, checkout_request_id: str):
      

        response = await self.daraja.stk_query(
            checkout_request_id=checkout_request_id
        )

        result_code = response.get("ResultCode")

        if result_code == "0":
            status = "SUCCESS"
        elif result_code == "1032":
            status = "CANCELLED"
        elif result_code == "1037":
            status = "TIMEOUT"
        elif result_code == "1":
            status = "INSUFFICIENT_FUNDS"
        else:
            status = "FAILED"

        return {
            "status": status,
            "result_code": result_code,
            "result_description": response.get("ResultDesc"),
            "checkout_request_id": checkout_request_id,
        }

    async def process_callback(self, payload: dict):
       

        callback = payload["Body"]["stkCallback"]

        checkout_request_id = callback["CheckoutRequestID"]
        merchant_request_id = callback["MerchantRequestID"]
        result_code = callback["ResultCode"]
        result_description = callback["ResultDesc"]

       
        if result_code != 0:
            return {
                "status": "FAILED",
                "checkout_request_id": checkout_request_id,
                "merchant_request_id": merchant_request_id,
                "result_code": result_code,
                "result_description": result_description,
            }

        metadata = callback["CallbackMetadata"]["Item"]

        # Convert Daraja's Item list into something easier to use.
        metadata_dict = {
            item["Name"]: item.get("Value")
            for item in metadata
        }

        return {
            "status": "SUCCESS",
            "checkout_request_id": checkout_request_id,
            "merchant_request_id": merchant_request_id,
            "result_code": result_code,
            "result_description": result_description,
            "amount": metadata_dict.get("Amount"),
            "mpesa_receipt_number": metadata_dict.get(
                "MpesaReceiptNumber"
            ),
            "transaction_date": metadata_dict.get(
                "TransactionDate"
            ),
            "phone_number": metadata_dict.get("PhoneNumber"),
        }

payment_service = PaymentService()
