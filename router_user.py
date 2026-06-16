from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Optional
import hashlib
import logging

from database import get_db_connection
from models import UserUpdate
from dependencies import verify_fixed_token, fetch_users, pwd_context

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
def root(token_data: dict = Depends(verify_fixed_token)):
    return {"message": "Hello world"}

@router.get("/api/test")
def test(token_data: dict = Depends(verify_fixed_token)):
    return {"message": "Hello from API"}

@router.get("/data/{user_id}")
def get_data(
    user_id: str,
    year_month: str | None = Query(None),
    token_data: dict = Depends(verify_fixed_token)
):
    data = fetch_users(user_id, year_month)
    return {
        "status": "success",
        "message": f"Data retrieved for {user_id}",
        "data": data,
        "meta": {
            "user": token_data
        }
    }

@router.get("/get/user_id")
def get_user_id(token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT user_id,employee_id,team FROM user"
            cursor.execute(sql)
            result = cursor.fetchall()
    return {
        "status": "success",
        "message": f"Data retrieved for user_id",
        "data": result
    }

@router.get("/get/role")
def get_role(token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM role_detail"
            cursor.execute(sql)
            result = cursor.fetchall()
    return {
        "status": "success",
        "message": f"Data retrieved for role",
        "data": result
    }

@router.get("/get/team")
def get_team(token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT team,remark FROM team_detail"
            cursor.execute(sql)
            result = cursor.fetchall()
    return {
        "status": "success",
        "message": f"Data retrieved for team",
        "data": result
    }

@router.put("/user/update")
def user_update(
    token_data: dict = Depends(verify_fixed_token),
    data: dict = Body(...),
):
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    fields = []
    values = []

    allowed_fields = [
        'employee_id', 'thai_initialname', 'thai_firstname', 'thai_lastname',
        'eng_initialname', 'eng_firstname', 'eng_lastname', 'email',
        'manager_id', 'approver_id', 'division', 'department', 'role_id',
        'team', 'shift_id', 'is_active', 'scheduled', 'password'
    ]

    for field in allowed_fields:
        if field in data:
            val = data.get(field)
            
            if field == "password":
                if val and str(val).strip() != "":
                    fields.append("`password`=%s")
                    values.append(pwd_context.hash(str(val)))
                continue

            fields.append(f"`{field}`=%s")
            
            if val is None or (isinstance(val, str) and val.strip() == ""):
                values.append(None)
            else:
                values.append(val)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    sql = f"UPDATE user SET {', '.join(fields)} WHERE user_id=%s"
    values.append(user_id)

    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, values)
                conn.commit()
                return {"status": "success", "message": "User updated successfully"}
    except Exception as e:
        logger.error(f"Database error in user_update: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/user/add")
def user_add(
    token_data: dict = Depends(verify_fixed_token),
    data: dict = Body(...),
):
    if not data.get("employee_id"):
        raise HTTPException(status_code=400, detail="Missing employee_id")

    fields = []
    placeholders = []
    values = []

    allowed_keys = [
        'employee_id', 'thai_initialname', 'thai_firstname', 'thai_lastname',
        'eng_initialname', 'eng_firstname', 'eng_lastname', 'email',
        'manager_id', 'approver_id', 'division', 'department', 'role_id',
        'team', 'shift_id', 'is_active', 'scheduled'
    ]

    for key in allowed_keys:
        val = data.get(key)
        
        fields.append(f"`{key}`")
        placeholders.append("%s")
        
        if val is None or (isinstance(val, str) and val.strip() == ""):
            values.append(None)
        else:
            values.append(val)

    fields.append("`password`")
    placeholders.append("%s")
    values.append(pwd_context.hash(str(data['employee_id'])))

    email_val = data.get('email')
    username_val = None
    
    if email_val and isinstance(email_val, str) and "@" in email_val:
        username_val = email_val.split('@')[0]
        
    fields.append("`username`")
    placeholders.append("%s")
    values.append(username_val)

    sql = f"INSERT INTO user ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id FROM user WHERE employee_id = %s", (data['employee_id'],))
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="Employee ID already exists")
                
                cursor.execute(sql, values)
                conn.commit()
                return {"status": "success", "message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in user_add: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/user/clear-login")
def clear_login(
    user_id: int = Query(..., description="The ID of the user to clear login info"),
    token_data: dict = Depends(verify_fixed_token)
):
    sql = "DELETE FROM users_login WHERE user_id = %s"
    
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    return {"status": "warning", "message": "No login session found for this user ID"}
                    
                return {"status": "success", "message": f"Login session cleared for user ID {user_id}"}
    except Exception as e:
        logger.error(f"Database error in clear_login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
