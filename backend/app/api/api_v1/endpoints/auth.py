from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ....db.session import get_db_dependency
from ....schemas.token import Token
from ....services.auth.jwt_provider import JWTAuthProvider

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
auth_provider = JWTAuthProvider()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_dependency)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    auth_result = await auth_provider.authenticate({"username": form_data.username, "password": form_data.password})
    
    if not auth_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = await auth_provider.generate_token(auth_result["user_id"])
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
