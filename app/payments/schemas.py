from pydantic import BaseModel,ConfigDict

class STKPushRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    phone_number: str
    amount: int
    account_reference: str 
    transaction_desc: str

class STKPushResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    success: bool
    message: str
    checkout_request_id: str | None = None
    merchant_request_id: str | None = None