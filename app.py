from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import qrcode
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # 請在生產環境中更改此密鑰
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///checkin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 數據模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    checkin_time = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/checkin', methods=['POST'])
def checkin():
    name = request.form.get('name')
    if not name:
        return jsonify({'status': 'error', 'message': '請輸入姓名'})
    
    participant = Participant.query.filter_by(name=name).first()
    if not participant:
        return jsonify({'status': 'error', 'message': '找不到此姓名，請確認姓名是否正確'})
    
    if participant.checkin_time:
        return jsonify({'status': 'error', 'message': '您已經報到過了'})
    
    participant.checkin_time = datetime.now()
    db.session.commit()
    return jsonify({'status': 'success', 'message': '報到成功！'})

@app.route('/admin')
@login_required
def admin():
    participants = Participant.query.all()
    return render_template('admin.html', participants=participants, os=os)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin'))
        flash('無效的用戶名或密碼')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_participant', methods=['POST'])
@login_required
def add_participant():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    if Participant.query.filter_by(email=email).first():
        return jsonify({'status': 'error', 'message': '此郵箱已被註冊'})
    
    participant = Participant(name=name, email=email, phone=phone)
    db.session.add(participant)
    db.session.commit()
    
    return jsonify({'status': 'success', 'message': '參與者添加成功'})

@app.route('/generate_event_qr')
@login_required
def generate_event_qr():
    # 生成活動 QR 碼
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"{request.host_url}")
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # 保存 QR 碼圖片
    qr_image.save("static/event_qr.png")
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # 創建管理員帳號（如果不存在）
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password_hash=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()
    
    # 確保靜態文件目錄存在
    os.makedirs('static', exist_ok=True)
    app.run(debug=True) 