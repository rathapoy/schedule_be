# ... existing code ...
        if not first_login:
            save_user_login(db_user, access_token, user.client_ip)

        return {
            "status": "success",
            "message": "System Login successful",
            "data": {
# ... existing code ...
                    "permission" : permission
                }
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"System login error: {str(e)}")
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
        
        try:
            if not pwd_context.verify(user.password, hashed):
                raise HTTPException(status_code=401, detail="Invalid username or password : 104")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid username or password : 105")

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
# ... existing code ...
                    "permission" : permission
                }
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/logout/{user_id}")
def logout(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
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
    except Exception as e:
        logger.error(f"Database error in logout: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/verify_token")
def verify_token(token: str = Depends(oauth2_scheme)):
# ... existing code ...
            return {
                "status": "valid",
                "user": {
                    "email": user_email,
                    "user_id": payload.get("user_id")
                }
            }

    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

@router.get("/check_token/{user_id}")
def check_token(user_id: str, token_data: dict = Depends(verify_fixed_token)):
    try:
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
    except Exception as e:
        logger.error(f"Database error in check_token: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reset_password")
def reset_password(data: UserLogin, token_data: dict = Depends(verify_fixed_token)):
    username = data.username
    password = data.password
    client_ip = data.client_ip
    
    if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$', password):
        raise HTTPException(status_code=400, detail="Password not strong enough")

    hashed = pwd_context.hash(password)

    try:
        with get_db_connection("account") as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user
                    SET password=%s
                    WHERE username=%s
                """, (hashed, username))
            conn.commit()
            
        db_user = get_user_from_db(username)
        if db_user:
            save_user_login(db_user, "", client_ip)
            
        return {
            "status": "success",
            "message": "Password reset success"
        }
    except Exception as e:
        logger.error(f"Database error in reset_password: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
