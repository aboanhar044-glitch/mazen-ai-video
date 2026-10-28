import streamlit as st
import datetime
import uuid

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="Mazen AI Video Generator",
    page_icon="🎬",
    layout="centered"
)

# ==================== قاعدة البيانات وإدارة الجلسات (في الذاكرة) ====================
ADMIN_PHONE = "779942299"
ADMIN_PASSWORD = "mmaa112000"

if "users_db" not in st.session_state:
    st.session_state.users_db = {}

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==================== واجهة المستخدم الجانبية (التنقل) ====================
st.sidebar.title("🧭 القائمة الرئيسية")
app_mode = st.sidebar.selectbox("اختر وضع الاستخدام:", ["🎬 توليد الفيديو (المستخدم)", "🔐 لوحة تحكم المدير"])

# ==================== 1. وضع توليد الفيديو (المستخدم) ====================
if app_mode == "🎬 توليد الفيديو (المستخدم)":
    st.title("🎬 Mazen AI Video Generator")
    st.write("أهلاً بك! أدخل رمز الدخول الخاص بك ووصف الفيديو للبدء في الإنتاج.")

    user_code = st.text_input("أدخل رمز الدخول (User Code):", type="password")
    
    if user_code:
        # التحقق من صلاحية المستخدم
        is_admin_master = (user_code == "ADMIN_MASTER_KEY")
        
        if not is_admin_master and user_code not in st.session_state.users_db:
            st.error("❌ الرمز السري غير صحيح أو غير موجود.")
        else:
            if is_admin_master:
                st.success("🔓 تم الدخول بصلاحيات المدير المطلقة.")
                is_admin = True
            else:
                user = st.session_state.users_db[user_code]
                
                if not user["is_active"]:
                    st.error("❌ تم إيقاف هذا الحساب من قبل المدير.")
                    st.stop()
                
                # التحقق من تاريخ انتهاء الصلاحية
                expiration_date = user["created_at"] + datetime.timedelta(days=user["valid_days"])
                if datetime.date.today() > expiration_date:
                    st.error("⏳ انتهت فترة الاشتراك الخاصة بك.")
                    st.stop()

                # تحديث العداد اليومي
                if user["last_used_date"] != datetime.date.today():
                    user["last_used_date"] = datetime.date.today()
                    user["videos_today"] = 0

                is_admin = False

            st.markdown("---")
            st.subheader("🛠️ إعدادات توليد الفيديو")
            
            prompt_text = st.text_area("أدخل نص/وصف الفيديو (Prompt):", placeholder="وصف تفصيلي للفيديو...")
            voice_name = st.selectbox("اختر الصوت (Voice Name):", ["Arabic_Male_1", "Arabic_Female_1", "Cinematic_Voice"])
            image_file = st.file_uploader("رفع صورة مرجعية اختيارية (Image File):", type=["png", "jpg", "jpeg"])
            duration_seconds = st.slider("مدة الفيديو بالثواني:", min_value=5, max_value=30, value=10)

            if not is_admin:
                user_data = st.session_state.users_db[user_code]
                remaining_videos = 3 - user_data["videos_today"]
                st.info(f"📊 رصيدك المتبقي لليوم: **{max(0, remaining_videos)} فيديوهات**")

            if st.button("🚀 بدء إنتاج الفيديو"):
                if not prompt_text.strip():
                    st.warning("الرجاء إدخال وصف الفيديو أولاً.")
                else:
                    # قيود المستخدم العادي
                    if not is_admin:
                        if user_data["videos_today"] >= 3:
                            st.error("⚠️ لقد استهلكت الحد الأقصى اليومي (3 فيديوهات). حاول غداً.")
                            st.stop()
                        if duration_seconds > 10:
                            duration_seconds = 10

                    with st.spinner("جاري معالجة وتوليد الفيديو بالذكاء الاصطناعي... يرجى الانتظار ⏳"):
                        # محاكاة عملية التوليد
                        import time
                        time.sleep(3)
                        
                        video_url = f"https://your-server.com/outputs/generated_video_{uuid.uuid4().hex[:6]}.mp4"
                        
                        if not is_admin:
                            user_data["videos_today"] += 1

                        st.success("🎉 تم إنتاج الفيديو بنجاح!")
                        st.markdown(f"🔗 **رابط التحميل المباشر:** [اضغط هنا للتحميل]({video_url})")
                        st.video(video_url)

# ==================== 2. لوحة تحكم المدير ====================
elif app_mode == "🔐 لوحة تحكم المدير":
    st.title("🔐 لوحة تحكم المدير")

    if not st.session_state.admin_logged_in:
        st.subheader("تسجيل دخول المدير")
        phone_input = st.text_input("رقم الهاتف:")
        password_input = st.text_input("كلمة المرور:", type="password")

        if st.button("دخول كمدير"):
            if phone_input == ADMIN_PHONE and password_input == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("أهلاً بك يا مدير! تم تسجيل الدخول بنجاح.")
                st.rerun()
            else:
                st.error("بيانات دخول المدير غير صحيحة.")
    else:
        st.success("✅ أنت مسجل الدخول بصلاحيات المدير.")
        if st.button("تسجيل الخروج"):
            st.session_state.admin_logged_in = False
            st.rerun()

        st.markdown("---")
        st.subheader("➕ توليد رمز جديد لمستخدم")
        
        custom_code_input = st.text_input("رمز مخصص (اختراقي - اتركه فارغاً للتوليد التلقائي):")
        valid_days_input = st.number_input("مدة الصلاحية بالأيام:", min_value=1, value=30)

        if st.button("إنشاء الرمز"):
            code = custom_code_input.strip() or str(uuid.uuid4())[:8]
            st.session_state.users_db[code] = {
                "valid_days": valid_days_input,
                "created_at": datetime.date.today(),
                "is_active": True,
                "videos_today": 0,
                "last_used_date": datetime.date.today()
            }
            st.success(f"تم إنشاء الرمز بنجاح: **`{code}`** (صالحة لمدة {valid_days_input} يوماً)")

        st.markdown("---")
        st.subheader("👥 إدارة المستخدمين الحاليين والرموز")
        
        if not st.session_state.users_db:
            st.info("لا توجد رموز مستخدمين مسجلة حتى الآن.")
        else:
            for code, data in list(st.session_state.users_db.items()):
                with st.expander(f"الرمز: {code} | الحالة: {'نشط ✅' if data['is_active'] else 'متوقف ❌'}"):
                    st.write(f"- أيام الصلاحية الكلية: {data['valid_days']}")
                    st.write(f"- تاريخ الإنشاء: {data['created_at']}")
                    st.write(f"- الفيديوهات المستخدمة اليوم: {data['videos_today']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"إيقاف الحساب", key=f"stop_{code}"):
                            data["is_active"] = False
                            st.rerun()
                    with col2:
                        if st.button(f"تفعيل الحساب", key=f"activate_{code}"):
                            data["is_active"] = True
                            st.rerun()
                    with col3:
                        extra_days = st.number_input(f"تمديد أيام لـ {code}", min_value=1, value=7, key=f"days_{code}")
                        if st.button(f"تأكيد التمديد", key=f"extend_{code}"):
                            data["valid_days"] += extra_days
                            data["is_active"] = True
                            st.success(تم تمديد الحساب بنجاح!)
                            st.rerun()
