from pydantic import BaseModel


class ChallengeRequest(BaseModel):
    wallet_address: str


class ChallengeResponse(BaseModel):
    wallet_address: str
    nonce: str


class VerifyRequest(BaseModel):
    wallet_address: str
    signature: str
    nonce: str
