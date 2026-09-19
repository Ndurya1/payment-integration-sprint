from fastapi import APIRouter, Request
from app.payments.service import  payment_service
from app.payments.schemas import STKPushRequest

router = APIRouter()

@router.post("/stk-push")
async def initiate_stk_payment(request: STKPushRequest):
    return await payment_service.initiate_stk_payment(
        phone_number=request.phone_number,
        amount=request.amount,
        account_reference=request.account_reference,
        transaction_desc=request.transaction_desc,
    )


@router.post("/callback")
async def mpesa_callback(payload: dict):
    await payment_service.process_callback(payload)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.get("/{checkout_request_id}/status")
async def payment_status(checkout_request_id: str):
    return await payment_service.query_stk_status(checkout_request_id)