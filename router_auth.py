from fastapi import APIRouter, Depends, HTTPException, status ,Header, Request
from datetime import timedelta
from jose import jwt, JWTError
from pydantic import BaseModel
import os
import re

from config import SKI, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, logger
from database import get_db_connection
from models import UserLogin, PasswordIn
from dependencies import (
    verify_fixed_token, pwd_context, create_access_token, 
    get_user_from_db, save_user_login, query_permission, oauth2_scheme, is_first_login
)

class SystemUserLogin(BaseModel):
    username: str
    client_ip: str | None = "0.0.0.0"

router = APIRouter()

@router.post("/hashpassword")
def hash_password(data: PasswordIn):
    if not data.password or len(data.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )
    hashed_password = pwd_context.hash(data.password)
    return {
        "status": "success",
        "hashed_password": hashed_password
    }

@router.post("/system_login")
def system_login(
    user: SystemUserLogin, 
    request: Request,
    x_internal_api_key: str | None = Header(None) 
):
    caller_ip = request.client.host 
    allowed_system_ip = os.getenv("ALLOW_SYSTEM_IP") 

    if allowed_system_ip and caller_ip != allowed_system_ip:
        raise HTTPException(status_code=403, detail=f"Forbidden: Unrecognized System IP ({caller_ip})")

    try:
        db_user = get_user_from_db(user.username)

        if not db_user:
            raise HTTPException(status_code=401, detail="User not found : Error 101")

        # ===== Login success =====
        access_token = create_access_token(
            data={
                "sub": str(db_user["user_id"]),
                "role": db_user["role_name"]
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        permission = query_permission(db_user)
        first_login = is_first_login(db_user["user_id"])

        if not first_login:
            save_user_login(db_user, access_token, user.client_ip)

        return {
            "status": "success",
            "message": "System Login successful",
            "data": {
                "first_login": first_login,
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "user_id": db_user["user_id"],
                    "emp_id": db_user["employee_id"],
                    "email": db_user["email"],
                    "name": db_user.get("eng_firstname"),
                    "role": db_user["role_name"],
                    "role_pr": db_user["role_priority"],
                    "division": db_user["division"],
                    "team": db_user["team"],
                    "shiftname": db_user["shift_name"],
                    "scheduled": db_user["scheduled"],
                    "permission" : permission
                }
            }
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
def login(user: UserLogin):
    try:
        db_user = get_user_from_db(user.username)

        if not db_user:
            raise HTTPException(status_code=401, detail="User not found : Error 101")

        hashed = db_user.get("password")
        if not hashed:
            raise HTTPException(status_code=401, detail="Password crash  : Error 102")
        
        # if isinstance(hashed, bytes):
        #     hashed = hashed.decode("utf-8")

        # if not hashed.startswith("$2"):
        #     raise HTTPException(status_code=401, detail="Not crypt : 103")

        try:
            if not pwd_context.verify(user.password, hashed):
                raise HTTPException(status_code=401, detail="Invalid username or password : 104")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid username or password : 105")

        # ===== Login success =====
        access_token = create_access_token(
            data={
                "sub": str(db_user["user_id"]),
                "role": db_user["role_name"]
            },
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        permission = query_permission(db_user)
        first_login = is_first_login(db_user["user_id"])

        if not first_login:
            save_user_login(db_user, access_token, user.client_ip)

        return {
            "status": "success",
            "message": "Login successful",
            "data": {
                "first_login": first_login,
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "user_id": db_user["user_id"],
                    "emp_id": db_user["employee_id"],
                    "email": db_user["email"],
                    "name": db_user.get("eng_firstname"),
                    "role": db_user["role_name"],
                    "role_pr": db_user["role_priority"],
                    "division": db_user["division"],
                    "team": db_user["team"],
                    "shiftname": db_user["shift_name"],
                    "scheduled": db_user["scheduled"],
                    "permission" : permission
                }
            }
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Login error")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/logout/{user_id}")
def logout(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = """
            UPDATE users_login
            SET login_token = NULL,
                login_ip = NULL
            WHERE user_id = %s
            """
            cursor.execute(sql, (user_id,))
        conn.commit()

    if cursor.rowcount == 0:
        return {"status": "ignored", "message": "user_id not found"}
    
    return {"status": "success", "message": "User logged out"}

@router.get("/verify_token")
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SKI, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject",
            )

        return {
            "status": "valid",
            "user": {
                "email": user_email,
                "user_id": payload.get("user_id")
            }
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.get("/check_token/{user_id}")
def check_token(user_id: str, token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT login_token FROM users_login WHERE user_id=%s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchall()
    return {
        "status": "success",
        "message": "check token",
        "data": result
    }

@router.post("/reset_password")
def reset_password(data: UserLogin, token_data: dict = Depends(verify_fixed_token)):
    username = data.username
    password = data.password
    client_ip = data.client_ip
    

    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        raise HTTPException(status_code=400, detail="Password not strong enough")

    hashed = pwd_context.hash(password)

    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE user
                SET password=%s
                WHERE username=%s
            """, (hashed, username))
        conn.commit()
    db_user = get_user_from_db(username)
    save_user_login(db_user, "", client_ip)
    return {
        "status": "success",
        "message": "Password reset success"
    }
