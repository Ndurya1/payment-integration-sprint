# app/payments/servic
from app.payments.daraja import DarajaClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.payments.repository import PaymentRepository


class PaymentService:
    def __init__(self):
        self.daraja = DarajaClient()

    async def initiate_stk_payment(
        self,
        db: AsyncSession,
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

        print("1. DARAJA RESPONSE:", response)

        # ResponseCode == 0 only means Safaricom accepted
        # the STK request for processing.
        if response.get("ResponseCode") != "0":
            print("2. STK REJECTED")
            return {
                "success": False,
                "message": "STK Push request was rejected",
                "data": response,
            }
        print("3. STK ACCEPTED")

        repository = PaymentRepository(db)
        print("4. REPOSITORY CREATED")

        payment = await repository.create_payment(
           phone_number=phone_number,
           amount=amount,
           account_reference=account_reference,
           merchant_request_id=response["MerchantRequestID"],
           checkout_request_id=response["CheckoutRequestID"],
        )

        print("5. PAYMENT CREATED:", payment)
        print("6. PAYMENT ID:", payment.id)

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

    async def process_callback(self, payload: dict, db: AsyncSession,):
        print(">>> CALLBACK RECEIVED")
        print(">>> CALLBACK PAYLOAD:", payload)

        callback = payload["Body"]["stkCallback"]
        checkout_request_id = callback["CheckoutRequestID"]
        merchant_request_id = callback["MerchantRequestID"]
        result_code = callback["ResultCode"]
        result_description = callback["ResultDesc"]

        print(">>> CHECKOUT ID:", checkout_request_id)
        print(">>> RESULT CODE:", result_code)

        repository = PaymentRepository(db)

        payment = await repository.get_by_checkout_request_id(
        checkout_request_id
    )
        print(">>> PAYMENT FOUND:", payment)
        if payment is None:
            print(">>> PAYMENT NOT FOUND")
            return {
            "success": False,
            "message": "Payment not found",
        },
    
        if result_code != 0:
            print(">>> UPDATING PAYMENT TO FAILED")

            await repository.update_payment_result(
                    payment=payment,
                    status="SUCCESS",
                    result_code=result_code,
                    result_description=result_description,
                    receipt_number=receipt_number,
                )
            print(">>> PAYMENT UPDATED TO FAILED")
         
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

        receipt_number = metadata_dict.get(
        "MpesaReceiptNumber"
    )

        await repository.update_payment_result(
        payment=payment,
        status="SUCCESS",
        result_code=result_code,
        result_description=result_description,
        receipt_number=receipt_number,
    )

        print(">>> PAYMENT UPDATED TO SUCCESS")

      

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
