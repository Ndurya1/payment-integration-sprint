from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.payments.models import Payment, PaymentStatus


class PaymentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db



    async def create_payment(
    self,
    phone_number: str,
    amount: int,
    account_reference: str,
    merchant_request_id: str,
    checkout_request_id: str,
):
     print("REPOSITORY: create_payment called")
     payment = Payment(
        phone_number=phone_number,
        amount=amount,
        account_reference=account_reference,
        merchant_request_id=merchant_request_id,
        checkout_request_id=checkout_request_id,
        status="PENDING",
    )
     print("REPOSITORY: payment object created")

     self.db.add(payment)
     print("REPOSITORY: added to session")

     await self.db.commit()
     print("REPOSITORY: COMMIT SUCCESSFUL")

     await self.db.refresh(payment)
     print("REPOSITORY: REFRESH SUCCESSFUL")
    

     return payment

    


    async def get_by_checkout_request_id(
    self,
    checkout_request_id: str,
):
     statement = select(Payment).where(
        Payment.checkout_request_id == checkout_request_id
    )

     result = await self.db.execute(statement)

     return result.scalar_one_or_none()

    async def update_payment_result(
    self,
    payment: Payment,
    status: str,
    result_code: int,
    result_description: str,
    receipt_number: str | None = None,
):
     payment.status = status
     payment.result_code = result_code
     payment.result_description = result_description
     payment.mpesa_receipt_number = receipt_number

     await self.db.commit()
     await self.db.refresh(payment)

     return payment