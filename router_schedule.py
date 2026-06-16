from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from typing import List, Optional
from datetime import datetime

from database import get_db_connection
from models import (
    ShiftDetail, WorkGroup, WorkSchedule, Holiday, 
    MonthSchedule, MonthConfig, RequestModel, OverrideBreakRequest, ManageSlotRequest
)
from dependencies import verify_fixed_token


from fastapi.responses import JSONResponse
from pydantic import BaseModel

import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.api_route("/schedule/shift", methods=["GET", "POST", "PUT", "DELETE"])
def shift_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    data: Optional[ShiftDetail] = Body(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:

            if action == "get":
                cursor.execute("""
                                SELECT 
                                    s.*,
                                    COUNT(u.user_id) AS user_count
                                FROM shift_detail AS s
                                LEFT JOIN account.user AS u
                                    ON s.shift_id = u.shift_id
                                GROUP BY s.shift_id, s.shift_name
                                """)
                result = cursor.fetchall()
                return {"status": "success", "data": result}

            elif action == "add" and data:
                sql = "INSERT INTO shift_detail (shift_name, shift_des, modify_by) VALUES (%s, %s, %s)"
                cursor.execute(sql, (data.shift_name, data.shift_des, data.modify_by))
                conn.commit()
                return {"status": "success", "message": "Shift added successfully"}

            elif action == "update" and data and data.shift_id:
                sql = "UPDATE shift_detail SET shift_name=%s, shift_des=%s, modify_by=%s WHERE shift_id=%s"
                cursor.execute(sql, (data.shift_name, data.shift_des, data.modify_by, data.shift_id))
                conn.commit()
                return {"status": "success", "message": "Shift updated successfully"}

            elif action == "delete" and data and data.shift_id:
                cursor.execute("DELETE FROM shift_detail WHERE shift_id=%s", (data.shift_id,))
                conn.commit()
                return {"status": "success", "message": "Shift deleted successfully"}

            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")


@router.api_route("/schedule/workgroup", methods=["GET", "POST", "PUT", "DELETE"])
def workgroup_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    data: Optional[WorkGroup] = Body(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:

            if action == "get" or (not action and data is None):
                # 2. ปรับ Query GET ให้ JOIN เอาชื่อ Break Slot มาด้วย
                base_sql = """
                    SELECT wg.*, bs.slot_name AS default_break_slot_name 
                    FROM work_group wg
                    LEFT JOIN break_slots bs ON wg.default_break_slot_id = bs.slot_id
                """
                if team:
                    cursor.execute(f"{base_sql} WHERE wg.team_workgroup = %s", (team,))
                else:
                    cursor.execute(base_sql)

                result = cursor.fetchall()
                return {"status": "success", "data": result}

            elif action == "add" and data:
                # 3. เพิ่ม default_break_slot_id ใน INSERT
                sql = """
                    INSERT INTO work_group (work_group, description, modify_by, team_workgroup, default_break_slot_id) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data.work_group, data.description, data.modify_by, 
                    data.team_workgroup, data.default_break_slot_id
                ))
                conn.commit()
                return {"status": "success", "message": "Work group added successfully"}

            elif action == "update" and data and data.work_group_id:
                # 4. เพิ่ม default_break_slot_id ใน UPDATE
                sql = """
                    UPDATE work_group 
                    SET work_group=%s, description=%s, modify_by=%s, team_workgroup=%s, default_break_slot_id=%s 
                    WHERE work_group_id=%s
                """
                cursor.execute(sql, (
                    data.work_group, data.description, data.modify_by, 
                    data.team_workgroup, data.default_break_slot_id, data.work_group_id
                ))
                conn.commit()
                return {"status": "success", "message": "Work group updated successfully"}

            elif action == "delete" and data and data.work_group_id:
                cursor.execute("DELETE FROM work_group WHERE work_group_id=%s", (data.work_group_id,))
                conn.commit()
                return {"status": "success", "message": "Work group deleted successfully"}

            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")

@router.api_route("/schedule/workschedule", methods=["GET", "POST", "PUT", "DELETE"])
def workschedule_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    data: Optional[WorkSchedule] = Body(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:

            if action == "get" or (not action and data is None):
                cursor.execute("SELECT * FROM work_schedule")
                result = cursor.fetchall()
                return {"status": "success", "data": result}

            elif action == "add" and data:
                sql = """INSERT INTO work_schedule 
                         (type_name, start_time, end_time, color, priority, sequence, ot_color, ot_hour, workdi_code, description, modify_by) 
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(sql, (
                    data.type_name, data.start_time, data.end_time, data.color, 
                    data.priority, data.sequence, data.ot_color, data.ot_hour, 
                    data.workdi_code, data.description, data.modify_by
                ))
                conn.commit()
                return {"status": "success", "message": "Work Schedule added successfully"}

            elif action == "update" and data and data.type_id:
                sql = """UPDATE work_schedule 
                         SET type_name=%s, start_time=%s, end_time=%s, color=%s, 
                             priority=%s, sequence=%s, ot_color=%s, ot_hour=%s, 
                             workdi_code=%s, description=%s, modify_by=%s 
                         WHERE type_id=%s"""
                cursor.execute(sql, (
                    data.type_name, data.start_time, data.end_time, data.color,
                    data.priority, data.sequence, data.ot_color, data.ot_hour, 
                    data.workdi_code, data.description, data.modify_by, data.type_id
                ))
                conn.commit()
                return {"status": "success", "message": "Work Schedule updated successfully"}

            elif action == "delete" and data and data.type_id:
                cursor.execute("DELETE FROM work_schedule WHERE type_id=%s", (data.type_id,))
                conn.commit()
                return {"status": "success", "message": "Work Schedule deleted successfully"}

            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")

@router.api_route("/schedule/team", methods=["GET", "POST", "PUT", "DELETE"])
def team_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    # data: Optional[team] = Body(None),
):
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:

            if action == "get" or (not action and data is None):
                cursor.execute("SELECT team FROM team_detail")
                result = cursor.fetchall()
                return {"status": "success", "data": result}

            # elif action == "add" and data:
            #     sql = "INSERT INTO work_schedule (type_name, start_time, end_time, color, description, modify_by) VALUES (%s, %s, %s, %s, %s, %s)"
            #     cursor.execute(sql, (data.type_name, data.start_time, data.end_time, data.color, data.description, data.modify_by))
            #     conn.commit()
            #     return {"status": "success", "message": "Work Schedule added successfully"}

            # elif action == "update" and data and data.type_id:
            #     sql = "UPDATE work_schedule SET type_name=%s, start_time=%s, end_time=%s, color=%s, description=%s, modify_by=%s WHERE type_id=%s"
            #     cursor.execute(sql, (data.type_name, data.start_time, data.end_time, data.color, data.description, data.modify_by, data.type_id))
            #     conn.commit()
            #     return {"status": "success", "message": "Work Schedule updated successfully"}

            # elif action == "delete" and data and data.type_id:
            #     cursor.execute("DELETE FROM work_schedule WHERE type_id=%s", (data.type_id,))
            #     conn.commit()
            #     return {"status": "success", "message": "Work Schedule deleted successfully"}

            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")

@router.api_route("/schedule/holiday", methods=["GET", "POST", "PUT", "DELETE"])
def holiday_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    data: Optional[Holiday] = Body(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:

            if action == "get" or (not action and data is None):
                if year:
                     cursor.execute("""
                        SELECT * FROM holiday 
                        WHERE YEAR(date) = %s
                    """, (year,))
                else:
                    cursor.execute("SELECT * FROM holiday")
                result = cursor.fetchall()
                return {"status": "success", "data": result}

            elif action == "add" and data:
                try:
                    sql = "INSERT INTO holiday (date, description) VALUES (%s, %s)"
                    cursor.execute(sql, (data.date, data.description))
                    conn.commit()
                    return {"status": "success", "message": "Holiday added successfully"}

                except Exception as e:
                    if "Duplicate entry" in str(e):
                        return {"status": "error", "message": "Date already exists."}
                    else:
                        return {"status": "error", "message": "Database error: " + str(e)}
            elif action == "update" and data and data.holiday_id:
                sql = "UPDATE holiday SET date=%s, description=%s  WHERE holiday_id=%s"
                cursor.execute(sql, (data.date, data.description, data.holiday_id))
                conn.commit()
                return {"status": "success", "message": "Holiday updated successfully"}

            elif action == "delete" and data and data.holiday_id:
                cursor.execute("DELETE FROM holiday WHERE holiday_id=%s", (data.holiday_id,))
                conn.commit()
                return {"status": "success", "message": "Holiday deleted successfully"}

            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")

@router.api_route("/schedule/monthschedule", methods=["GET", "POST", "PUT", "DELETE"])
def monthschedule_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    schedule_date: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    team: Optional[str] = Query(None),
    priority: Optional[int] = Query(None),
    schedule_status: Optional[str] = Query(None),
    schedule_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    data: Optional[MonthSchedule] = Body(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:

            if action == "get" or (not action and data is None):
                
                select_columns = """
                    s.*, 
                    u.employee_id, u.thai_initialname, u.thai_firstname, u.thai_lastname, u.email, u.shift_id, u.team,u.approver_id,
                    sd.shift_name, sd.shift_des,
                    wg.work_group, wg.description AS work_group_desc,
                    ws.type_name, ws.start_time, ws.end_time, ws.color, ws.priority,ws.sequence, ws.description AS schedule_desc,ws.workdi_code AS workdi_code
                """
                
                query = f"""
                    SELECT {select_columns} 
                    FROM noc_schedule AS s 
                    LEFT JOIN account.user AS u ON s.user_id = u.user_id
                    LEFT JOIN shift_detail AS sd ON u.shift_id = sd.shift_id
                    LEFT JOIN work_group AS wg ON s.work_group_id = wg.work_group_id
                    LEFT JOIN work_schedule AS ws ON s.work_schedule_id = ws.type_id
                """
                
                params = []
                where_clauses = []

                if month is not None:
                    if "-" in month:
                        try:
                            ym = datetime.strptime(month, "%Y-%m")
                            where_clauses.append("YEAR(s.schedule_date) = %s")
                            where_clauses.append("MONTH(s.schedule_date) = %s")
                            params.extend([ym.year, ym.month])
                        except ValueError:
                            raise HTTPException(
                                status_code=400,
                                detail="Month parameter must be in format YYYY-MM or number 1-12"
                            )
                    else:
                        try:
                            month_int = int(month)
                            if not 1 <= month_int <= 12:
                                raise ValueError
                            where_clauses.append("MONTH(s.schedule_date) = %s")
                            params.append(month_int)
                        except ValueError:
                            raise HTTPException(
                                status_code=400,
                                detail="Month parameter must be a valid number (1-12) or YYYY-MM"
                            )
                if schedule_id is not None:
                    try:
                        where_clauses.append("s.schedule_id = %s")
                        params.append(int(schedule_id))
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail="Schedule_id must be a valid integer"
                        )
                if schedule_date is not None:
                    try:
                        where_clauses.append("s.schedule_date LIKE %s")
                        params.append(schedule_date)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail="schedule_date error"
                        )
                if team is not None:
                    try:
                        where_clauses.append("u.team LIKE %s")
                        params.append(team)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail="team error"
                        )
                if priority is not None:
                    try:
                        where_clauses.append("ws.priority LIKE %s")
                        params.append(priority)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail="priority error"
                        )
                if schedule_status is not None:
                    try:
                        where_clauses.append("s.status = %s")
                        params.append(schedule_status)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail="schedule_status error"
                        )
                if user_id is not None:
                    try:
                        where_clauses.append("s.user_id = %s")
                        params.append(user_id)
                    except ValueError:
                        raise HTTPException(
                            status_code=400,
                            detail="user_id error"
                        )
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

                cursor.execute(query, tuple(params))
                result = cursor.fetchall()
                return {"status": "success", "data": result}
            elif action == "change_status" and data and data.schedule_id and data.status:
                fields = ["status = %s"]
                params = [data.status]

                if data.remark is not None:
                    fields.append("remark = %s")
                    params.append(data.remark)

                params.append(data.schedule_id)

                sql = f"""
                    UPDATE noc_schedule
                    SET {", ".join(fields)}
                    WHERE noc_schedule.schedule_id = %s
                """

                cursor.execute(sql, tuple(params))
                conn.commit()

                return {
                    "status": "success",
                    "message": "Schedule updated successfully"
                }
            elif action == "confirm_swap":
                if not data or not data.schedule_id or not data.user_id or not data.status:
                    raise HTTPException(status_code=400, detail="Missing required fields")

                cursor.execute(
                    """
                    UPDATE noc_schedule
                    SET user_id = %s,
                        status = %s
                    WHERE schedule_id = %s
                    """,
                    (data.user_id , data.status , data.schedule_id)
                )
                conn.commit()
                return {"status": "success", "message": "Updated swap data."}
            elif action == "delete":
                sid = None
                if data and getattr(data, "schedule_id", None):
                    sid = data.schedule_id
                elif schedule_id:
                    sid = schedule_id
                if sid:
                    cursor.execute("DELETE FROM noc_schedule WHERE schedule_id = %s",(sid,))
                    deleted_rows = cursor.rowcount
                    conn.commit()
                    return {
                        "status": "success",
                        "message": f"Schedule {sid} deleted successfully"
                    }
                if not month:
                    raise HTTPException(status_code=400,detail="Month is required for delete operation")
                try:
                    datetime.strptime(month, "%Y-%m")
                except ValueError:
                    raise HTTPException(status_code=400,detail="Month parameter must be in format YYYY-MM")
                sql = """
                    DELETE s
                    FROM noc_schedule s
                    JOIN account.user u
                        ON s.user_id = u.user_id
                    WHERE s.schedule_date LIKE %s
                """
                params = [f"{month}%"]
                if team:
                    sql += " AND u.team = %s"
                    params.append(team)

                cursor.execute(sql, tuple(params))
                deleted_rows = cursor.rowcount
                conn.commit()

                return {
                    "status": "success",
                    "message": (
                        f"Deleted {deleted_rows} schedules "
                        f"for month {month}"
                        + (f" (team: {team})" if team else "")
                    )
                }
            else:
                raise HTTPException(status_code=400,detail="Invalid request or missing parameters")

@router.post("/api/update/schedule")
def upsert_monthschedule(
    token_data: dict = Depends(verify_fixed_token),
    schedules: List[MonthSchedule] = Body(...),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            try:
                update_rows = []
                insert_rows = []

                for s in schedules:
                    if s.schedule_id:
                        update_rows.append((
                            s.user_id,
                            s.work_schedule_id,
                            s.work_group_id,
                            s.schedule_date,
                            s.status,
                            s.remark,
                            s.schedule_id
                        ))
                    else:
                        insert_rows.append((
                            s.user_id,
                            s.work_schedule_id,
                            s.work_group_id,
                            s.schedule_date,
                            s.status,
                            s.remark
                        ))

                # 🔹 BULK UPDATE
                if update_rows:
                    update_sql = """
                        UPDATE noc_schedule
                        SET 
                            user_id = %s,
                            work_schedule_id = %s,
                            work_group_id = %s,
                            schedule_date = %s,
                            status = %s,
                            remark = %s,
                            last_update = CURRENT_TIMESTAMP
                        WHERE schedule_id = %s
                    """
                    cursor.executemany(update_sql, update_rows)

                # 🔹 BULK INSERT / UPSERT
                if insert_rows:
                    insert_sql = """
                        INSERT INTO noc_schedule 
                        (user_id, work_schedule_id, work_group_id, schedule_date, status, remark)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            work_schedule_id = VALUES(work_schedule_id),
                            work_group_id = VALUES(work_group_id),
                            status = VALUES(status),
                            remark = VALUES(remark),
                            last_update = CURRENT_TIMESTAMP
                    """
                    cursor.executemany(insert_sql, insert_rows)

                conn.commit()

                return {
                    "status": "success",
                    "message": f"{len(schedules)} rows inserted/updated"
                }

            except Exception as e:
                conn.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/schedule/month/config", methods=["GET", "POST", "PUT", "DELETE"])
def monthly_config_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    data: Optional[MonthConfig] = Body(None),
    monthyear: Optional[str] = Query(None),
):
    # เชื่อมต่อ Database schedule สำหรับ Config ทั่วไป
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            if action == "get":
                select_cols = "config_id, team_config, month_year, is_enabled, is_locked, modify_by, last_update"
                
                if monthyear:
                    query = f"SELECT {select_cols} FROM month_config WHERE month_year=%s"
                    cursor.execute(query, (monthyear,)) 
                else:
                    query = f"SELECT {select_cols} FROM month_config"
                    cursor.execute(query)
                
                result = cursor.fetchall()
                return {"status": "success", "data": result}

            elif action == "get_teams":
                # [ใหม่] เชื่อมต่อ Database account เพื่อดึง Team Detail
                # ใช้ context manager แยกออกมาเพื่อ connect ไปยัง database account
                try:
                    with get_db_connection("account") as conn_acc:
                        with conn_acc.cursor() as cursor_acc:
                            cursor_acc.execute("SELECT team, remark FROM team_detail ORDER BY team ASC")
                            teams = cursor_acc.fetchall()
                            return {"status": "success", "data": teams}
                except Exception as e:
                     return {"status": "error", "message": f"Failed to fetch teams: {str(e)}"}

            elif action == "add" and data:
                sql = "INSERT INTO month_config (month_year, team_config, is_enabled, is_locked, modify_by) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (data.month_year, data.team_config, data.is_enabled, data.is_locked, data.modify_by))
                conn.commit()
                return {"status": "success", "message": "Month Config added successfully"}

            elif action == "update" and data:
                if data.config_id:
                    sql = "UPDATE month_config SET is_enabled=%s, is_locked=%s, modify_by=%s WHERE config_id=%s"
                    cursor.execute(sql, (data.is_enabled, data.is_locked, data.modify_by, data.config_id))
                    conn.commit()
                    return {"status": "success", "message": "Month Config updated successfully"}
                
                elif data.month_year:
                    sql = "UPDATE month_config SET is_enabled=%s, is_locked=%s, modify_by=%s WHERE month_year=%s"
                    cursor.execute(sql, (data.is_enabled, data.is_locked, data.modify_by, data.month_year))
                    conn.commit()
                    return {"status": "success", "message": "Month Config updated successfully (All teams in month)"}
                else:
                    return {"status": "error", "message": "No valid identifier (config_id or month_year) provided."}

            elif action == "delete" and data and data.config_id:
                cursor.execute("DELETE FROM month_config WHERE config_id=%s", (data.config_id,))
                conn.commit()
                return {"status": "success", "message": "Month Config deleted successfully"}

            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")

@router.api_route("/api/request", methods=["GET", "POST", "PUT", "DELETE"])
def request_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    data: Optional[RequestModel] = Body(None),
    request_id: Optional[int] = Query(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            # 1. GET (All or Single by ID)
            if action == "get" or (not action and data is None):
                if request_id:
                    cursor.execute("SELECT * FROM `request_view` WHERE request_id=%s", (request_id,))
                else:
                    cursor.execute("SELECT * FROM `request_view` ORDER BY request_id DESC")
                result = cursor.fetchall()
                return {"status": "success", "data": result}
            
            # 2. GET USER INFO
            elif action == "getinfo_userid":
                if not data or not data.request_user_id:
                    raise HTTPException(status_code=400, detail="request_user_id is required")
                cursor.execute(
                    "SELECT * FROM request_view WHERE request_user_id=%s ORDER BY date_time_created DESC",
                    (data.request_user_id,)
                )
                result = cursor.fetchall()
                return {"status": "success", "data": result}
            
            # 3. GET TARGET (For Swap/Standby checks/task check)
            elif action == "get-task":
                if not data or not data.user_replace_id :
                    raise HTTPException(
                        status_code=400,
                        detail="user_replace_id and approver_user_id are required"
                    )

                cursor.execute(
                        """
                        SELECT *
                        FROM request_view
                        WHERE (
                                (user_replace_id=%s AND user_replace_confirm IS NULL)
                            OR (approver_user_id=%s AND date_approve IS NULL)
                            )
                        AND request_status = 'Pending'
                        """,
                        (data.user_replace_id, data.user_replace_id)
                    )

                result = cursor.fetchall()
                count = len(result)

                return {
                    "status": "success",
                    "count": count,
                    "data": result
                }
            elif action == "gettarget":
                if not data or not data.schedule_id:
                    raise HTTPException(status_code=400, detail="schedule_id is required")

                cursor.execute(
                    "SELECT * FROM request_view WHERE target_schedule_id=%s AND request_status=%s",
                    (data.schedule_id, "Pending")
                )
                result = cursor.fetchall()
                return {"status": "success", "data": result}
            # 4. GET INFO (Check logic - now supports fetching by request_id via query or schedule_id via body)
            elif action == "getinfo":
                # Special Case: If PHP sends request_id via Query String for this action
                if request_id:
                    cursor.execute("SELECT * FROM request_view WHERE request_id=%s", (request_id,))
                    result = cursor.fetchall()
                    return {"status": "success", "data": result}

                # Default Case: By Schedule ID
                if not data or not data.schedule_id:
                    raise HTTPException(status_code=400, detail="schedule_id is required")

                cursor.execute(
                    "SELECT * FROM request_view WHERE schedule_id=%s AND request_status = %s",
                    (data.schedule_id, "Pending")
                )
                result = cursor.fetchall()
                return {"status": "success", "data": result}
            
            # 5. ADD REQUEST
            elif action == "add" and data:
                try:
                    payload = data.dict(exclude_none=True)
                    if "request_id" in payload:
                        del payload["request_id"] # Let DB handle auto-increment

                    if not payload:
                        raise HTTPException(status_code=400, detail="No data to insert")

                    columns = ", ".join(payload.keys())
                    placeholders = ", ".join(["%s"] * len(payload))
                    values = tuple(payload.values())

                    sql = f"""
                        INSERT INTO requests ({columns})
                        VALUES ({placeholders})
                    """

                    cursor.execute(sql, values)
                    conn.commit()

                    return {"status": "success", "message": "Request created successfully"}

                except Exception as e:
                    return {"status": "error", "message": str(e)}
            
            # 6. UPDATE REQUEST
            elif action == "update":
                if not data or not data.request_id:
                    raise HTTPException(status_code=400, detail="request_id is required")

                payload = data.dict(exclude_none=True)
                r_id = payload.pop("request_id")

                if not payload:
                     return {"status": "success", "message": "No changes."}

                set_clause = ", ".join([f"{k}=%s" for k in payload.keys()])
                values = tuple(payload.values()) + (r_id,)

                sql = f"UPDATE requests SET {set_clause} WHERE request_id=%s"
                cursor.execute(sql, values)
                conn.commit()

                return {"status": "success", "message": "Updated request."}
            else:
                raise HTTPException(status_code=400, detail="Invalid request or missing parameters")

@router.api_route("/api/request_type", methods=["GET", "POST", "PUT", "DELETE"])
def request_type_handler(
    token_data: dict = Depends(verify_fixed_token),
    action: Optional[str] = Query(None),
    reqid: Optional[int] = Query(None),
    data: Optional[RequestModel] = Body(None),
):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            if action == "get" or (not action and reqid is None and data is None):
                cursor.execute(
                    "SELECT * FROM request_type WHERE request_type_id > 1"
                )
                result = cursor.fetchall()
                return {"status": "success", "data": result}

            elif reqid is not None and reqid > 1:
                cursor.execute(
                    "SELECT * FROM request_type WHERE request_type_id = %s",
                    (reqid,)
                )
                result = cursor.fetchone()
                return {"status": "success", "data": result}

            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request or missing parameters"
                )

@router.get("/api/overtime")
def get_overtime(month: str = None,token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM ot_view"
            params = []

            if month:

                sql += " WHERE LEFT(schedule_date, 7) = %s"
                params.append(month) 
            
            cursor.execute(sql, params)
            result = cursor.fetchall()
            return {"status": "success", "data": result}

@router.get("/api/cur-month-schedule")
def get_todaysch(token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM Cur_date_sch_v"
            cursor.execute(sql)
            result = cursor.fetchall()
            return {"status": "success", "data": result}

@router.get("/api/cur-day-schedule")
def get_todaysch(token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM date_seat_v"
            cursor.execute(sql)
            result = cursor.fetchall()
            return {"status": "success", "data": result}

@router.get("/api/break-slots")
def get_break_slots(token_data: dict = Depends(verify_fixed_token)):
    with get_db_connection("schedule") as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    slot_id, 
                    slot_name, 
                    TIME_FORMAT(start_time, '%H:%i:%s') AS start_time, 
                    TIME_FORMAT(end_time, '%H:%i:%s') AS end_time 
                FROM break_slots 
                WHERE is_active = 1
                ORDER BY start_time ASC
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            return {"status": "success", "data": result}



@router.post("/api/override-break")
def override_break_slot(req: OverrideBreakRequest, token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("schedule") as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO daily_break_overrides 
                    (schedule_date, user_id, override_slot_id, modify_by)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    override_slot_id = VALUES(override_slot_id),
                    modify_by = VALUES(modify_by)
                """
                
                modifier = str(req.modify_by) if req.modify_by else "system"
                
                logger.info(f"User {modifier} is overriding: Target User {req.user_id}, Date {req.schedule_date}")
                
                cursor.execute(sql, (
                    req.schedule_date, 
                    req.user_id, 
                    req.override_slot_id, 
                    modifier
                ))
                conn.commit()
                
                return {
                    "status": "success", 
                    "message": "break time update success."
                }
    except Exception as e:
        error_detail = traceback.format_exc()
        logger.error(f"Detailed Error: {error_detail}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database Error: {str(e)}"
        )
@router.get("/api/all-break-slots")
def get_all_break_slots(token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("schedule") as conn:
            with conn.cursor() as cursor:
                # สังเกตว่าจะไม่มี WHERE is_active = 1 เพราะต้องการให้หน้าจัดการเห็นทั้งหมด
                sql = """
                    SELECT slot_id, slot_name, 
                           TIME_FORMAT(start_time, '%H:%i:%s') AS start_time, 
                           TIME_FORMAT(end_time, '%H:%i:%s') AS end_time,
                           is_active
                    FROM break_slots 
                    ORDER BY start_time ASC, slot_id ASC
                """
                cursor.execute(sql)
                return {"status": "success", "data": cursor.fetchall()}
    except Exception as e:
        logger.error(f"Fetch All Slots Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 3. Endpoint: Single POST สำหรับ Add, Edit, Delete
@router.post("/api/manage-break-slots")
def manage_break_slots(req: ManageSlotRequest, token_data: dict = Depends(verify_fixed_token)):
    try:
        with get_db_connection("schedule") as conn:
            with conn.cursor() as cursor:
                
   
                if req.action == "create":
                    sql = """
                        INSERT INTO break_slots (slot_name, start_time, end_time, is_active) 
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(sql, (req.slot_name, req.start_time, req.end_time, req.is_active))
                    msg = "สร้าง Break Slot สำเร็จ"
                    
                elif req.action == "update":
                    sql = """
                        UPDATE break_slots 
                        SET slot_name=%s, start_time=%s, end_time=%s, is_active=%s 
                        WHERE slot_id=%s
                    """
                    cursor.execute(sql, (req.slot_name, req.start_time, req.end_time, req.is_active, req.slot_id))
                    msg = "แก้ไข Break Slot สำเร็จ"
                    
                elif req.action == "delete":
                    sql = "DELETE FROM break_slots WHERE slot_id=%s"
                    cursor.execute(sql, (req.slot_id,))
                    msg = "ลบ Break Slot สำเร็จ"
                    
                else:
                    raise ValueError("Action ไม่ถูกต้อง (ต้องเป็น create, update หรือ delete)")
                

                conn.commit()
                
                return {"status": "success", "message": msg}
                
    except Exception as e:
        logger.error(f"Manage Break Slot Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))