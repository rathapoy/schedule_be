from pydantic import BaseModel, Field
from typing import Optional
from datetime import time

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str
    client_ip: str

class UserUpdate(BaseModel):
    user_id: Optional[int] = None
    employee_id: Optional[str] = None
    thai_initialname: Optional[str] = None
    thai_firstname: Optional[str] = None
    thai_lastname: Optional[str] = None
    eng_initialname: Optional[str] = None
    eng_firstname: Optional[str] = None
    eng_lastname: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    manager_id: Optional[int] = None
    approver_id: Optional[int] = None
    department: Optional[str] = None
    division: Optional[str] = None
    role_id: Optional[int] = None
    team: Optional[str] = None
    shift_id: Optional[int] = None
    password: Optional[str] = None
    is_active: Optional[int] = None
    scheduled: Optional[int] = None

class PasswordIn(BaseModel):
    password: str

# Schedule Models
class ShiftDetail(BaseModel):
    shift_id: Optional[int] = None
    shift_name: Optional[str] = None
    shift_des: Optional[str] = None
    modify_by: Optional[str] = None

class WorkGroup(BaseModel):
    work_group_id: Optional[int] = None
    work_group: str
    team_workgroup: str
    description: Optional[str] = None
    default_break_slot_id: Optional[int] = None  # เพิ่มฟิลด์นี้
    last_modified: Optional[str] = None 
    modify_by: Optional[str] = None

class WorkSchedule(BaseModel):
    type_id: Optional[int] = None
    type_name: str = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    color: Optional[str] = None
    priority: Optional[int] = 0
    sequence: Optional[int] = 0
    ot_color: Optional[str] = None
    ot_hour: Optional[int] = None
    workdi_code: Optional[str] = None
    description: Optional[str] = None
    last_modified: Optional[str] = None 
    modify_by: Optional[str] = None

class MonthSchedule(BaseModel):
    schedule_id: Optional[int] = None
    user_id: Optional[int] = None
    work_schedule_id: Optional[int] = None
    work_group_id: Optional[int] = None
    schedule_date: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None
    last_update: Optional[str] = None 

class MonthConfig(BaseModel):
    config_id: Optional[int] = None
    team_config: Optional[str] = None
    month_year: Optional[str] = None
    is_enabled: Optional[int] = None
    is_locked: Optional[int] = None
    modify_by: Optional[str] = None
    last_update: Optional[str] = None 

class Holiday(BaseModel):
    holiday_id: Optional[int] = None
    date: Optional[str] = None
    description: Optional[str] = None 

class RequestModel(BaseModel):
    request_id: Optional[int] = None
    schedule_id: Optional[int] = None
    target_schedule_id: Optional[int] = None
    request_type_id: Optional[int] = None
    request_user_id: Optional[int] = None
    user_replace_id: Optional[int] = None
    user_replace_confirm: Optional[int] = None
    date_confirm: Optional[str] = None
    approver_user_id: Optional[int] = None
    date_approve: Optional[str] = None
    reason_for_rejection: Optional[str] = None
    request_reason: Optional[str] = None
    request_status: Optional[str] = None

class RequestTypeModel(BaseModel):  
    request_type_id: Optional[int] = None
    request_type_name: Optional[str] = None
    quota: Optional[int] = None
    quota_period: Optional[str] = None
    modified_by: Optional[str] = None

class PermissionUpdate(BaseModel):
    role_id: int
    permission_ids: list[int]



class AnnounceData(BaseModel):
    icon: str = Field(..., max_length=100)
    detail: str = Field(..., min_length=1)
    status: str = None

class OverrideBreakRequest(BaseModel):
    schedule_date: str
    user_id: int
    override_slot_id: int
    modify_by: str 
    
class ManageSlotRequest(BaseModel):
    action: str  # ต้องเป็น 'create', 'update', หรือ 'delete'
    slot_id: Optional[int] = 0
    slot_name: Optional[str] = ""
    start_time: Optional[str] = ""
    end_time: Optional[str] = ""
    is_active: Optional[int] = 1