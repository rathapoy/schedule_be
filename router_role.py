from fastapi import APIRouter, HTTPException, Depends
from database import get_db_connection 
from models import PermissionUpdate 
from dependencies import verify_fixed_token
from pydantic import BaseModel
from typing import Optional
import traceback

router = APIRouter()


class RoleData(BaseModel):
    role_name: str
    role_priority: int
    font_color: Optional[str] = "#000000"
    icon: Optional[str] = ""

class PermissionData(BaseModel):
    permission_name: str
    description: Optional[str] = ""

@router.get("/api/role-matrix")
def get_role_matrix(token_data: dict = Depends(verify_fixed_token)):
    try:
        # ใช้รูปแบบเดียวกับ get_user_id ที่คุณใช้งานได้
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                # 1. ดึง Roles
                cursor.execute("SELECT * FROM role_detail ORDER BY role_priority ASC")
                roles = cursor.fetchall()

                # 2. ดึง Permissions
                cursor.execute("SELECT * FROM permissions_detail")
                permissions = cursor.fetchall()

                # 3. ดึง Mapping
                cursor.execute("SELECT role_id, permission_id FROM role_setup")
                mapping = cursor.fetchall()

        return {
            "status": "success",
            "data": {
                "roles": roles,
                "permissions": permissions,
                "mapping": mapping
            }
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/roles")
def create_role(data: RoleData, token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO role_detail (role_name, role_priority, font_color, icon) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (data.role_name, data.role_priority, data.font_color, data.icon))
                conn.commit()
        return {"status": "success", "message": "Role created"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/roles/{role_id}")
def update_role(role_id: int, data: RoleData, token_data: dict = Depends(verify_fixed_token)):
    try:
        if role_id == 0: raise HTTPException(status_code=403, detail="Cannot edit Superadmin")
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE role_detail SET role_name=%s, role_priority=%s, font_color=%s, icon=%s WHERE role_id=%s"
                cursor.execute(sql, (data.role_name, data.role_priority, data.font_color, data.icon, role_id))
                conn.commit()
        return {"status": "success", "message": "Role updated"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/roles/{role_id}")
def delete_role(role_id: int, token_data: dict = Depends(verify_fixed_token)):
    try:
        if role_id == 0: raise HTTPException(status_code=403, detail="Cannot delete Superadmin")
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM role_detail WHERE role_id=%s", (role_id,))
                conn.commit()
        return {"status": "success", "message": "Role deleted"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/permissions")
def create_permission(data: PermissionData, token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                sql = "INSERT INTO permissions_detail (permission_name, description) VALUES (%s, %s)"
                cursor.execute(sql, (data.permission_name, data.description))
                conn.commit()
        return {"status": "success", "message": "Permission created"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/permissions/{perm_id}")
def update_permission(perm_id: int, data: PermissionData, token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                sql = "UPDATE permissions_detail SET permission_name=%s, description=%s WHERE permission_id=%s"
                cursor.execute(sql, (data.permission_name, data.description, perm_id))
                conn.commit()
        return {"status": "success", "message": "Permission updated"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/permissions/{perm_id}")
def delete_permission(perm_id: int, token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM permissions_detail WHERE permission_id=%s", (perm_id,))
                conn.commit()
        return {"status": "success", "message": "Permission deleted"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/update-permissions")
def update_permissions(data: PermissionUpdate, token_data: dict = Depends(verify_fixed_token)):
    try:
        if data.role_id == 0: raise HTTPException(status_code=403, detail="Cannot modify Superadmin")
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM role_setup WHERE role_id = %s", (data.role_id,))
                if data.permission_ids:
                    sql = "INSERT INTO role_setup (role_id, permission_id, remark) VALUES (%s, %s, %s)"
                    values = [(data.role_id, p_id, 'Updated via Matrix') for p_id in data.permission_ids]
                    cursor.executemany(sql, values)
                conn.commit()
        return {"status": "success", "message": "Mapping updated"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))