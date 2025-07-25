import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import sqlite3
from dotenv import load_dotenv
load_dotenv()
DB_PATH = os.getenv('DB_PATH')
ADMIN_USERS = os.getenv('ADMIN_USERS').split(',')
ADMIN_PASSWORDS = os.getenv('ADMIN_PASSWORDS').split(',')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
import importlib.util

app = Flask(__name__)
app.secret_key = 'supersecretkey'
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class AdminUser(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    for idx, username in enumerate(ADMIN_USERS):
        if str(idx) == user_id:
            return AdminUser(id=idx, username=username)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        for idx, (u, p) in enumerate(zip(ADMIN_USERS, ADMIN_PASSWORDS)):
            if username == u and password == p:
                user = AdminUser(id=idx, username=u)
                login_user(user)
                return redirect(url_for('orders'))
        flash('Неверный логин или пароль', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def orders():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, phone, address, material, area, extras, photos, date, time, comment, price, status FROM orders ORDER BY created_at DESC')
    orders = c.fetchall()
    conn.close()
    response = make_response(render_template('orders.html', orders=orders))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/update_status', methods=['POST'])
@login_required
def update_status():
    order_id = request.form['order_id']
    status = request.form['status']
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
    conn.commit()
    conn.close()
    return ('', 204)

@app.route('/delete_order', methods=['POST'])
@login_required
def delete_order():
    order_id = request.form.get('order_id')
    if order_id:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM orders WHERE id=?', (order_id,))
        conn.commit()
        conn.close()
        flash('Заявка удалена!', 'success')
    return redirect(url_for('orders'))

@app.route('/contractors')
@login_required
def contractors():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, phone, telegram_id FROM contractors ORDER BY id')
    contractors = c.fetchall()
    conn.close()
    return render_template('contractors.html', contractors=contractors)

@app.route('/add_contractor', methods=['POST'])
@login_required
def add_contractor():
    name = request.form.get('contractor_name')
    phone = request.form.get('contractor_phone')
    telegram_id = request.form.get('contractor_telegram')

    if name and phone:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO contractors (name, phone, telegram_id) VALUES (?, ?, ?)',
                 (name, phone, telegram_id if telegram_id else None))
        conn.commit()
        conn.close()
        flash('Подрядчик добавлен!', 'success')
    else:
        flash('Заполните обязательные поля!', 'danger')

    return redirect(url_for('contractors'))

@app.route('/edit_contractor/<int:contractor_id>', methods=['GET', 'POST'])
@login_required
def edit_contractor(contractor_id):
    if request.method == 'POST':
        name = request.form.get('contractor_name')
        phone = request.form.get('contractor_phone')
        telegram_id = request.form.get('contractor_telegram')

        if name and phone:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE contractors SET name=?, phone=?, telegram_id=? WHERE id=?',
                     (name, phone, telegram_id if telegram_id else None, contractor_id))
            conn.commit()
            conn.close()
            flash('Подрядчик обновлен!', 'success')
            return redirect(url_for('contractors'))
        else:
            flash('Заполните обязательные поля!', 'danger')
    
    # GET запрос - показываем форму редактирования
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, phone, telegram_id FROM contractors WHERE id=?', (contractor_id,))
    contractor = c.fetchone()
    conn.close()
    
    if not contractor:
        flash('Подрядчик не найден!', 'danger')
        return redirect(url_for('contractors'))
    
    return render_template('edit_contractor.html', contractor=contractor)

@app.route('/delete_contractor', methods=['POST'])
@login_required
def delete_contractor():
    contractor_id = request.form.get('contractor_id')
    if contractor_id:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM contractors WHERE id=?', (contractor_id,))
        conn.commit()
        conn.close()
        flash('Подрядчик удален!', 'success')
    return redirect(url_for('contractors'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # Получаем абсолютный путь к папке uploads
    upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'uploads')
    return send_from_directory(upload_path, filename)

@app.route('/weekends', methods=['GET', 'POST'])
@login_required
def weekends():
    from datetime import datetime
    import calendar
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Получаем месяц и год из query-параметров
    year = int(request.args.get('year', datetime.today().year))
    month = int(request.args.get('month', datetime.today().month))
    if request.method == 'POST':
        selected = request.form.getlist('weekend')
        c.execute('DELETE FROM weekends WHERE strftime("%Y-%m", date) = ?', (f'{year:04d}-{month:02d}',))
        for d in selected:
            c.execute('INSERT OR IGNORE INTO weekends (date) VALUES (?)', (d,))
        conn.commit()
        flash('Выходные сохранены!', 'success')
    # Календарь на выбранный месяц
    cal = calendar.monthcalendar(year, month)
    days = []
    for week in cal:
        week_days = []
        for day in week:
            if day == 0:
                week_days.append(None)
            else:
                week_days.append(datetime(year, month, day))
        days.append(week_days)
    c.execute('SELECT date FROM weekends')
    weekends_set = set(row[0] for row in c.fetchall())
    conn.close()
    prev_month = (month - 1) or 12
    prev_year = year - 1 if month == 1 else year
    next_month = (month % 12) + 1
    next_year = year + 1 if month == 12 else year
    return render_template('weekends.html', days=days, weekends_set=weekends_set, year=year, month=month, prev_year=prev_year, prev_month=prev_month, next_year=next_year, next_month=next_month, today=datetime.today().date())

@app.route('/prices', methods=['GET', 'POST'])
def prices():
    # Динамически загружаем материалы и доп. услуги
    spec = importlib.util.spec_from_file_location('materials', 'bot/materials.py')
    materials_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(materials_mod)
    MATERIALS = dict(materials_mod.MATERIALS)
    EXTRAS = dict(materials_mod.EXTRAS)
    if request.method == 'POST':
        # Обновляем существующие материалы
        new_materials = {}
        for i in range(len(request.form.getlist('material_name'))):
            name = request.form.getlist('material_name')[i].strip()
            price = request.form.getlist('material_price')[i].strip()
            if name and price.isdigit():
                new_materials[name] = int(price)
        # Обновляем существующие услуги
        new_extras = {}
        for i in range(len(request.form.getlist('extra_name'))):
            name = request.form.getlist('extra_name')[i].strip()
            price = request.form.getlist('extra_price')[i].strip()
            if name and price.isdigit():
                new_extras[name] = int(price)
        # Добавляем новые материал/услугу если заполнены
        new_mat_name = request.form.get('new_material_name', '').strip()
        new_mat_price = request.form.get('new_material_price', '').strip()
        if new_mat_name and new_mat_price.isdigit():
            new_materials[new_mat_name] = int(new_mat_price)
        new_extra_name = request.form.get('new_extra_name', '').strip()
        new_extra_price = request.form.get('new_extra_price', '').strip()
        if new_extra_name and new_extra_price.isdigit():
            new_extras[new_extra_name] = int(new_extra_price)
        # Сохраняем в файл
        with open('bot/materials.py', 'w', encoding='utf-8') as f:
            f.write('MATERIALS = '+repr(new_materials)+'\n\n')
            f.write('EXTRAS = '+repr(new_extras)+'\n')
        flash('Цены и услуги успешно обновлены!', 'success')
        return redirect(url_for('prices'))
    return render_template('prices.html', materials=MATERIALS, extras=EXTRAS)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 