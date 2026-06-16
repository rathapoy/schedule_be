import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import jwt


from config import SKI, ALGORITHM, API_TOKEN_USER, logger
from database import get_db_connection

# Security Schemes
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# --- Auth Helpers ---
def verify_fixed_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != API_TOKEN_USER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SKI, algorithm=ALGORITHM)

# --- Database Helpers ---
def get_user_from_db(username: str):
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    u.*, 
                    r.role_name,
                    r.role_priority,
                    s.shift_name
                FROM account.user AS u
                JOIN account.role_detail AS r ON u.role_id = r.role_id
                LEFT JOIN schedule.shift_detail AS s ON u.shift_id = s.shift_id
                WHERE u.username LIKE %s 
                  AND u.is_active = 1
            """
            cursor.execute(sql, (username,))
            return cursor.fetchone()

def query_permission(db_user: dict):
    role_id = db_user.get("role_id")
    if not role_id:
        return []
    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT pd.permission_name
                FROM role_setup AS rs
                JOIN role_detail AS rd ON rd.role_id = rs.role_id
                JOIN permissions_detail AS pd ON pd.permission_id = rs.permission_id
                WHERE rs.role_id = %s
            """
            cursor.execute(sql, (role_id,))
            rows = cursor.fetchall()
    permissions = [row['permission_name'] for row in rows]
    return permissions

def save_user_login(db_user: dict, access_token: str, ip_address: str = None):
    user_id = db_user.get("user_id")
    username = db_user.get("username")
    login_time = datetime.now(ZoneInfo("Asia/Bangkok"))

    if not user_id:
        raise ValueError("user_id is required")

    with get_db_connection("account") as conn:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO users_login (user_id, username, login_token, login_ip, login_timestamp)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                login_token = VALUES(login_token),
                login_ip = VALUES(login_ip),
                login_timestamp = VALUES(login_timestamp)
            """
            cursor.execute(sql, (user_id, username, access_token, ip_address, login_time))
            conn.commit()

def is_first_login(user_id: int) -> bool:
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                sql = """
                SELECT 1
                FROM users_login
                WHERE user_id = %s
                LIMIT 1
                """
                cursor.execute(sql, (user_id,))
                row = cursor.fetchone()
        return row is None

    except Exception:
        logger.exception("is_first_login error")
        return True



def fetch_users(user_id: str, year_month: str | None = None):
    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                base_query = """
                    SELECT 
                        u.*, 
                        r.role_name,
                        s.shift_name,
                        CONCAT(m.thai_firstname, ' ', m.thai_lastname) AS manager_name,
                        CONCAT(a.thai_firstname, ' ', a.thai_lastname) AS approver_name
                    FROM account.user AS u
                    LEFT JOIN account.role_detail AS r ON u.role_id = r.role_id
                    LEFT JOIN account.user AS m ON u.manager_id = m.user_id
                    LEFT JOIN account.user AS a ON u.approver_id = a.user_id
                    LEFT JOIN schedule.shift_detail AS s ON u.shift_id = s.shift_id
                """

                if user_id == "all":
                    query = base_query + " ORDER BY u.employee_id"
                    params = ()
                elif user_id == "active":
                    query = base_query + " WHERE u.is_active = 1 ORDER BY u.employee_id"
                    params = ()
                elif user_id == "inactive":
                    query = base_query + " WHERE u.is_active = 0 ORDER BY u.employee_id"
                    params = ()
                elif user_id == "schedule":
                    if year_month:
                        month_date = datetime.strptime(year_month + "-01", "%Y-%m-%d")
                        query = base_query + """
                            WHERE u.scheduled = 1
                              AND (
                                    u.resign_date IS NULL
                                    OR u.resign_date >= %s
                                  )
                            ORDER BY u.employee_id
                        """
                        params = (month_date,)
                    else:
                        query = base_query + " WHERE u.scheduled = 1 AND u.is_active = 1 ORDER BY u.employee_id"
                        params = ()
                elif user_id == "sup":
                    query = (
                        "SELECT user_id, employee_id, thai_firstname, thai_lastname "
                        "FROM user "
                        "WHERE team = 'SUP' "
                        "ORDER BY employee_id"
                    )
                    params = ()
                else:
                    query = base_query + " WHERE u.employee_id = %s ORDER BY u.employee_id"
                    params = (user_id,)

                cursor.execute(query, params)
                result = cursor.fetchall()

        for row in result:
            row.pop("password", None)

        return result

    except Exception as e:
        print("Error in fetch_users:", e)
        return []