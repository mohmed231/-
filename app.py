import streamlit as st
import pandas as pd
import datetime
import sqlite3
import urllib.parse

# 1. تهيئة وتحديث قاعدة البيانات (SQLite) لتشمل الجداول المالية
conn = sqlite3.connect('smart_center_financial.db', check_same_thread=False)
cursor = conn.cursor()

# إنشاء جداول قاعدة البيانات (الطلاب، الحضور، الإعدادات، الفواتير المالية)
cursor.execute('''CREATE TABLE IF NOT EXISTS students 
                  (code TEXT PRIMARY KEY, name TEXT, class_level TEXT, phone TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS attendance 
                  (timestamp TEXT, code TEXT, name TEXT, class_level TEXT, status TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS settings 
                  (key TEXT PRIMARY KEY, value TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS invoices 
                  (invoice_id TEXT PRIMARY KEY, code TEXT, name TEXT, class_level TEXT, month_name TEXT, amount REAL, payment_date TEXT)''')
conn.commit()

# إدراج قوالب الرسائل الافتراضية للتحضير والفواتير
cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('whatsapp_msg', 'السلام عليكم ورحمة الله وبركاته، نحيطكم علماً بوصل الطالب(ة): [الاسم] المقيد بصف: [الصف] إلى قاعة الدرس بنجاح في تمام الساعة: [الوقت].')")
cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('whatsapp_invoice_msg', 'السلام عليكم ورحمة الله وبركاته، تم استلام مصاريف شهر: [الشهر] للطالب(ة): [الاسم] بقيمة: [المبلغ] جنيهاً بنجاح. رقم الفاتورة: [الفاتورة].')")
conn.commit()

# إعداد أسعار الحصص الافتراضية لكل مرحلة (يمكنك تعديل القيم هنا مباشرة)
fees_dict = {
    "الرابع الابتدائي": 150.0,
    "الخامس الابتدائي": 150.0,
    "السادس الابتدائي": 150.0,
    "الأول الإعدادي": 200.0,
    "الثاني الإعدادي": 200.0,
    "الثالث الإعدادي": 250.0
}

# إعدادات الواجهة البصرية للموقع الإلكتروني
st.set_page_config(page_title="منصة الأستاذة إيناس معتمد المالية", layout="wide")
st.markdown("<h1 style='text-align: center; color: #1E3A8A; font-family: Tahoma;'>✨ موقع منصة الأستاذة إيناس معتمد الذكي ✨</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: #6B7280; font-family: Tahoma;'>إدارة المجموعات، الحضور، والنظام المالي المطور</h4>", unsafe_allow_html=True)
st.write("---")

# 2. القائمة الجانبية للتنقل بين شاشات الموقع
st.sidebar.markdown("<h3 style='text-align: center; color: #1E3A8A;'>🗂️ أقسام الموقع</h3>", unsafe_allow_html=True)
menu = ["🏠 لوحة التحكم والباركود", "💳 الخزينة والفواتير المالية", "👥 تسجيل الطلاب والصفوف", "📝 سجل الحضور العام", "⚙️ إعدادات رسائل الواتساب"]
choice = st.sidebar.radio("", menu)

# ---------------------------------------------------------
# الشاشة الأولى: لوحة التحكم وجهاز مسح الباركود
# ---------------------------------------------------------
if choice == "🏠 لوحة التحكم والباركود":
    st.subheader("💳 مسح كروت الباركود - رصد الحضور الفوري")
    barcode_input = st.text_input("ضع مؤشر الماوس هنا، ثم ابدأ بمسح كارت الطالب بالقارئ:", key="barcode", value="")
    
    if barcode_input:
        cursor.execute("SELECT name, class_level, phone FROM students WHERE code=?", (barcode_input,))
        student = cursor.fetchone()
        
        if student:
            s_name, s_class, s_phone = student
            now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("INSERT INTO attendance VALUES (?, ?, ?, ?, 'حضور')", (now_time, barcode_input, s_name, s_class))
            conn.commit()
            
            st.success(f"✅ تم رصد حضور الطالب بنجاح: {s_name} ({s_class})")
            
            cursor.execute("SELECT value FROM settings WHERE key='whatsapp_msg'")
            base_msg = cursor.fetchone()[0]
            
            final_msg = base_msg.replace("[الاسم]", f"*{s_name}*").replace("[الصف]", f"*{s_class}*").replace("[الوقت]", datetime.datetime.now().strftime("%I:%M %p"))
            final_msg += "\n\n✨ *منصة الأستاذة إيناس معتمد - معلمة لغة عربية مُعتمَدة* ✨"
            
            encoded_msg = urllib.parse.quote(final_msg)
            whatsapp_url = f"https://whatsapp.com{s_phone}&text={encoded_msg}"
            
            st.markdown(f'<a href="{whatsapp_url}" target="_blank" style="display: inline-block; background-color: #25D366; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 10px;">📲 إرسال تنبيه الحضور الفوري عبر WhatsApp</a>', unsafe_allow_html=True)
        else:
            st.error("❌ تنبيه: كود الباركود هذا غير مسجل في قاعدة بيانات المنصة!")

# ---------------------------------------------------------
# الشاشة الثانية: الخزينة والفواتير المالية (التحديث المطور)
# ---------------------------------------------------------
elif choice == "💳 الخزينة والفواتير المالية":
    st.subheader("💰 لوحة الإيرادات والتقارير المالية للسنتر")
    
    # 1. عرض كروت الإحصائيات المالية الذكية
    cursor.execute("SELECT SUM(amount) FROM invoices")
    total_revenue = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT COUNT(invoice_id) FROM invoices")
    total_invoices = cursor.fetchone()[0] or 0
    
    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("💵 إجمالي إيرادات السنتر الكلية", f"{total_revenue:,.2f} جنيهاً")
    col_stat2.metric("🧾 إجمالي عدد الفواتير المصدرة", f"{total_invoices} فاتورة")
    
    st.write("---")
    
    # 2. نموذج تحصيل المصروفات وإصدار الفواتير
    st.subheader("🧾 تسجيل دفع شهري وإصدار فاتورة جديدة")
    col_inv1, col_inv2 = st.columns(2)
    
    with col_inv1:
        inv_student_code = st.text_input("ادخلي كود الطالب المسدد للمصاريف:")
        inv_month = st.selectbox("اشتراك شهر:", ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"])
    
    # التحقق التلقائي من الطالب وعرض سعره الخاص بمرحلته
    student_found = False
    inv_name, inv_class, inv_phone, auto_amount = "", "", "", 0.0
    if inv_student_code:
        cursor.execute("SELECT name, class_level, phone FROM students WHERE code=?", (inv_student_code,))
        res = cursor.fetchone()
        if res:
            inv_name, inv_class, inv_phone = res
            auto_amount = fees_dict.get(inv_class, 0.0)
            student_found = True
            with col_inv2:
                st.info(f"👤 الطالب: {inv_name} | 🏫 الصف: {inv_class}")
                inv_amount = st.number_input("المبلغ المطلوب دفعه (تم جلبه تلقائياً):", value=auto_amount)
        else:
            with col_inv2:
                st.error("❌ هذا الكود غير مسجل بنظام الطلاب!")

    if st.button("💾 اعتماد عملية الدفع وإصدار الفاتورة"):
        if student_found:
            inv_id = f"INV-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            p_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            cursor.execute("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?)", (inv_id, inv_student_code, inv_name, inv_class, inv_month, inv_amount, p_date))
            conn.commit()
            st.success(f"🎉 تم تسجيل الفاتورة {inv_id} بنجاح بمبلغ {inv_amount} جنيهاً!")
            
            # جلب نص رسالة الفاتورة وصياغتها للواتساب
            cursor.execute("SELECT value FROM settings WHERE key='whatsapp_invoice_msg'")
            inv_template = cursor.fetchone()[0]
            
            final_inv_msg = inv_template.replace("[الاسم]", f"*{inv_name}*").replace("[الشهر]", f"*{inv_month}*").replace("[المبلغ]", f"*{inv_amount}*").replace("[الفاتورة]", f"*{inv_id}*")
            final_inv_msg += "\n\n✨ *منصة الأستاذة إيناس معتمد - معلمة لغة عربية مُعتمَدة* ✨"
            
            encoded_inv_msg = urllib.parse.quote(final_inv_msg)
            whatsapp_inv_url = f"https://whatsapp.com{inv_phone}&text={encoded_inv_msg}"
            
            st.markdown(f'<a href="{whatsapp_inv_url}" target="_blank" style="display: inline-block; background-color: #25D366; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 10px;">📲 إرسال فاتورة الدفع الفورية لولي الأمر عبر WhatsApp</a>', unsafe_allow_html=True)
            
    st.write("---")
    st.subheader("📊 أرشيف الفواتير التفصيلي")
    df_invoices = pd.read_sql_query("SELECT invoice_id as 'رقم الفاتورة', code as 'كود الطالب', name as 'اسم الطالب', class_level as 'الصف الدراسي', month_name as 'الشهر', amount as 'المبلغ المدفوع', payment_date as 'تاريخ السداد' FROM invoices ORDER BY payment_date DESC", conn)
    st.dataframe(df_invoices, use_container_width=True)

# ---------------------------------------------------------
# الشاشة الثالثة: تسجيل وإدارة بيانات الطلاب والصفوف
# ---------------------------------------------------------
elif choice == "👥 تسجيل الطلاب والصفوف":
    st.subheader("📝 إضافة طالب جديد لمجموعات السنتر")
    col1, col2 = st.columns(2)
    with col1:
        s_code = st.text_input("كود الباركود الفريد للكارت (مثال: 4001):")
        s_name = st.text_input("اسم الطالب ثلاثي:")
    with col2:
        s_class = st.selectbox("الصف الدراسي والمجموعة:", list(fees_dict.keys()))
        s_phone = st.text_input("رقم هاتف ولي الأمر (بالصيغة الدولية مثل: 201012345678):")
        
    if st.button("💾 حفظ الطالب في قاعدة بيانات الموقع"):
        if s_code and s_name and s_phone:
            try:
                cursor.execute("INSERT INTO students VALUES (?, ?, ?, ?)", (s_code, s_name, s_class, s_phone))
                conn.commit()
                st.success(f"🎉 تم تسجيل الطالب {s_name} بنجاح.")
            except sqlite3.IntegrityError:
                st.error("⚠️ خطأ: كود الباركود هذا مخصص لطالب آخر مسجل مسبقاً!")
                
    st.write("---")
    df_students = pd.read_sql_query("SELECT code as 'كود الباركود', name as 'اسم الطالب', class_level as 'الصف الدراسي', phone as 'رقم هاتف ولي الأمر' FROM students", conn)
    st.dataframe(df_students, use_container_width=True)

# ---------------------------------------------------------
# الشاشة الرابعة: سجل الحضور العام والتقارير
