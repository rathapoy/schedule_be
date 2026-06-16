from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router_auth import router as auth_router
from router_user import router as user_router
from router_schedule import router as schedule_router
from router_tts import router as tts_router
from router_role import router as role_router
from router_announce import router as announce_router
from router_contact import router as contact_router
from router_serviceorder import router as serviceorder_router
from router_pppoe import router as pppoe_router
from router_telnet import router as telnet_router
from router_nocticket import router as nocticket_router
from router_chtkstatus import router as chtkstatus_router
from router_bot import router as bot_router
from router_cof import router as cof_router
from router_inc_remark import router as inc_remark_router
from router_generate_config import router as generate_config_router
from router_log import router as log_router


app = FastAPI()

#CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://10.233.97.85,https://10.233.97.84").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, # เอา "*" ออก
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(schedule_router)
app.include_router(tts_router)
app.include_router(role_router)
app.include_router(announce_router)
app.include_router(contact_router)
app.include_router(serviceorder_router)
app.include_router(pppoe_router)
app.include_router(telnet_router)
app.include_router(nocticket_router)
app.include_router(chtkstatus_router)
app.include_router(bot_router)
app.include_router(cof_router)
app.include_router(inc_remark_router)
app.include_router(generate_config_router)
app.include_router(log_router)
# Root Endpoint (Optional fallback if not covered in user_router)
@app.get("/health")
def health_check():
    return {"status": "ok"}
