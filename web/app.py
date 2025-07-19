import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import sqlite3
from config import DB_PATH, ADMIN_USERS, ADMIN_PASSWORDS, UPLOAD_FOLDER

app = Flask(__name__)
app.secret_key = 'supersecretkey'
login_manager = LoginManager(app)

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
        return render_template('login.html', error='Неверный логин или пароль')
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
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders = c.fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

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

if __name__ == '__main__':
    app.run(debug=True) 