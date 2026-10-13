from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.db.session import get_db
from app.services import auth_service

router = APIRouter(prefix="/auth")

SESSION_COOKIE = "gmit_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_agent = request.headers.get("user-agent")
    token = auth_service.create_session(db, user, user_agent)

    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # set True in production behind HTTPS
        path="/",
    )
    return {"ok": True, "user": {"id": str(user.id), "email": user.email}}


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db), token: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if token:
        auth_service.delete_session(db, token)
    response.delete_cookie(SESSION_COOKIE)
    return {"ok": True}


@router.get("/me")
def me(db: Session = Depends(get_db), token: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = auth_service.get_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    return {"id": str(session.user.id), "email": session.user.email}
