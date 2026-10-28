import datetime
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from pydantic import BaseModel
import requests

app = FastAPI(title="Mazen AI Video Generator")

# ==================== قاعدة البيانات (مؤقتة في الذاكرة - يمكن ربطها بـ SQLite/PostgreSQL) ====================

ADMIN_PHONE = "779942299"
ADMIN_PASSWORD = "mmaa112000"

# الهيكل: { "code_123": {"days_valid": 30, "created_at": date, "is_active": True, "videos_today": 0, "last_used_date": date} }
users_db = {}
admin_sessions = set()

# ==================== Pydantic Models ====================

class AdminLogin(BaseModel):
    phone: str
    password: str

class GenerateUserCode(BaseModel):
    custom_code: Optional[str] = None
    valid_days: int

class UpdateUserCode(BaseModel):
    user_code: str
    action: str  # "extend", "stop", "activate"
    additional_days: Optional[int] = 0

# ==================== مصادقة المدير والمستخدمين ====================

@app.post("/admin/login")
def admin_login(data: AdminLogin):
    if data.phone == ADMIN_PHONE and data.password == ADMIN_PASSWORD:
        session_token = str(uuid.uuid4())
        admin_sessions.add(session_token)
        return {"status": "success", "message": "أهلاً بك يا مدير", "admin_token": session_token}
    raise HTTPException(status_code=401, detail="بيانات دخول المدير غير صحيحة")

def verify_admin(x_admin_token: str = Header(...)):
    if x_admin_token not in admin_sessions:
        raise HTTPException(status_code=403, detail="غير مسموح. صلاحية المدير مطلوبة")
    return True

def verify_user_access(x_user_code: str = Header(...)):
    # التحقق هل هو المدير؟
    if x_user_code == "ADMIN_MASTER_KEY":
        return {"is_admin": True}

    if x_user_code not in users_db:
        raise HTTPException(status_code=401, detail="الرمز السري غير صحيح أو غير موجود")
    
    user = users_db[x_user_code]
    
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="تم إيقاف هذا الحساب من قبل المدير")
    
    # التحقق من تاريخ انتهاء الصلاحية
    expiration_date = user["created_at"] + datetime.timedelta(days=user["valid_days"])
    if datetime.date.today() > expiration_date:
        raise HTTPException(status_code=403, detail="انتهت فترة الاشتراك الخاصة بك")

    # تحديث وتعديل العداد اليومي
    if user["last_used_date"] != datetime.date.today():
        user["last_used_date"] = datetime.date.today()
        user["videos_today"] = 0

    return {"is_admin": False, "user_data": user, "code": x_user_code}

# ==================== لوحة تحكم المدير ====================

@app.post("/admin/generate-code", dependencies=[Depends(verify_admin)])
def create_code(data: GenerateUserCode):
    code = data.custom_code or str(uuid.uuid4())[:8]
    users_db[code] = {
        "valid_days": data.valid_days,
        "created_at": datetime.date.today(),
        "is_active": True,
        "videos_today": 0,
        "last_used_date": datetime.date.today()
    }
    return {"status": "success", "user_code": code, "valid_days": data.valid_days}

@app.post("/admin/manage-user", dependencies=[Depends(verify_admin)])
def manage_user(data: UpdateUserCode):
    if data.user_code not in users_db:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    
    user = users_db[data.user_code]
    if data.action == "stop":
        user["is_active"] = False
    elif data.action == "activate":
        user["is_active"] = True
    elif data.action == "extend":
        user["valid_days"] += data.additional_days
        user["is_active"] = True

    return {"status": "success", "message": f"تم تحديث الحساب {data.user_code} بنجاح", "user": user}

# ==================== محرك إنتاج الفيديو بالذكاء الاصطناعي ====================

@app.post("/generate-video")
async def generate_video(
    prompt_text: str = Form(...),
    voice_name: Optional[str] = Form("Arabic_Male_1"),
    image_file: Optional[UploadFile] = File(None),
    duration_seconds: int = Form(10),
    auth_info: dict = Depends(verify_user_access)
):
    is_admin = auth_info["is_admin"]

    # تطبيق القيود على المستخدم العادي
    if not is_admin:
        user = auth_info["user_data"]
        if user["videos_today"] >= 3:
            raise HTTPException(status_code=429, detail="لقد استهلكت الحد الأقصى اليومي (3 فيديوهات). حاول غداً.")
        if duration_seconds > 10:
            duration_seconds = 10 # إجبار المدة على 10 ثوانٍ كحد أقصى

    # --- التكامل مع خدمات الذكاء الاصطناعي الحقيقية (AI Generation Logic) ---
    # 1. تحويل النص إلى صوت بالصوت المطلوب (مثل ElevenLabs API)
    # 2. توليد الفيديو من النص أو الصورة (مثل RunwayML API / HeyGen / Luma API)
    
    # محاكاة العملية وإرجاع رابط تنزيل مباشر
    video_url = f"https://your-server.com/outputs/generated_video_{uuid.uuid4().hex[:6]}.mp4"

    if not is_admin:
        auth_info["user_data"]["videos_today"] += 1

    return {
        "status": "success",
        "message": "تم إنتاج الفيديو بنجاح!",
        "video_url": video_url,
        "remaining_daily_videos": (3 - auth_info["user_data"]["videos_today"]) if not is_admin else "غير محدود"
        }

if __name__ == "__main__":
     import uvicorn
     uvicorn.run("PythonApplication1:app", host="127.0.0.1", port=8000, reload=True)