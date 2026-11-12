import os
import sqlite3
import imghdr
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Configuration
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
DB_PATH = os.path.join(BASE_DIR, 'database.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

# Ensure directories exist on D:
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = 'teachers_secret_key_' + os.urandom(16).hex()

# Admin credentials (default: admin / 123456)
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', '123456')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            image_filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin():
    return session.get('is_admin', False)

@app.route('/')
def index():
    conn = get_db()
    teachers = conn.execute('SELECT * FROM teachers ORDER BY id DESC').fetchall()
    count = len(teachers)
    conn.close()
    return render_template('index.html', teachers=teachers, count=count, is_admin=is_admin())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['is_admin'] = True
            flash('تم تسجيل الدخول كمسؤول بنجاح', 'success')
            return redirect(url_for('index'))
        else:
            flash('بيانات الدخول غير صحيحة', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('index'))

@app.route('/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route('/add', methods=['POST'])
def add_teacher():
    if 'photo' not in request.files:
        flash('يرجى اختيار صورة للمدرس', 'error')
        return redirect(url_for('index'))
        
    file = request.files['photo']
    name = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    
    if file.filename == '' or not name or not specialization:
        flash('جميع الحقول مطلوبة (الاسم، التخصص، والصورة)', 'error')
        return redirect(url_for('index'))
        
    if not allowed_file(file.filename):
        flash('نوع الملف غير مسموح به! يُسمح فقط بالصور (PNG, JPG, JPEG, GIF, WEBP)', 'error')
        return redirect(url_for('index'))
        
    raw_filename = secure_filename(file.filename) or 'teacher.jpg'
    base, ext = os.path.splitext(raw_filename)
    counter = 1
    filename = f"{base}{ext}"
    while os.path.exists(os.path.join(IMAGES_DIR, filename)):
        filename = f"{base}_{counter}{ext}"
        counter += 1
        
    save_path = os.path.join(IMAGES_DIR, filename)
    file.save(save_path)
    
    # Check if the uploaded file is really a valid image
    img_type = imghdr.what(save_path)
    if not img_type and not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
        try:
            os.remove(save_path)
        except OSError:
            pass
        flash('الملف المرفوع ليس صورة صالحة!', 'error')
        return redirect(url_for('index'))
        
    conn = get_db()
    conn.execute('INSERT INTO teachers (name, specialization, image_filename) VALUES (?, ?, ?)',
                 (name, specialization, filename))
    conn.commit()
    conn.close()
    
    flash('تمت إضافة المدرس بنجاح', 'success')
    return redirect(url_for('index'))

@app.route('/edit/<int:teacher_id>', methods=['POST'])
def edit_teacher(teacher_id):
    name = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    
    if not name or not specialization:
        flash('الاسم والتخصص مطلوبان', 'error')
        return redirect(url_for('index'))
        
    conn = get_db()
    conn.execute('UPDATE teachers SET name = ?, specialization = ? WHERE id = ?',
                 (name, specialization, teacher_id))
    conn.commit()
    conn.close()
    
    flash('تم تعديل بيانات المدرس بنجاح', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    # Only admin can delete teachers
    if not is_admin():
        flash('عذراً، حذف المدرسين يتطلب تسجيل الدخول كمسؤول', 'error')
        return redirect(url_for('login'))
        
    conn = get_db()
    teacher = conn.execute('SELECT image_filename FROM teachers WHERE id = ?', (teacher_id,)).fetchone()
    if teacher:
        img_path = os.path.join(IMAGES_DIR, teacher['image_filename'])
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
        except OSError:
            pass
        conn.execute('DELETE FROM teachers WHERE id = ?', (teacher_id,))
        conn.commit()
        flash('تم حذف المدرس بنجاح', 'success')
    else:
        flash('المدرس غير موجود', 'error')
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
