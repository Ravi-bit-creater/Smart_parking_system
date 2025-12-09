from flask import Flask, render_template, request, redirect, flash, session
from config import get_connection
import pymysql
from datetime import datetime

app = Flask(__name__)
app.secret_key = "my_super_secret_key_123"

@app.route('/')
def home():
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO user (name, email, password, role) 
            VALUES (%s, %s, %s, 'user')
        """
        cursor.execute(insert_query, (name, email, password))
        conn.commit()

        flash("Registration Successful! You can now login.")
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)

        query = "SELECT * FROM user WHERE email = %s AND password = %s"
        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if user:
            session['user_name'] = user['name']
            session['user_id'] = user['user_id']
            session['role'] = user['role']   # 🔥 ROLE SAVED IN SESSION
            flash("Login Successful!")
            return redirect('/dashboard')
        else:
            flash("Invalid email or password!")
            return redirect('/login')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    vehicle_search = request.args.get('vehicle_search')
    zone_filter = request.args.get('zone_filter')

    query = """
        SELECT ps.slot_id, ps.slot_number, ps.slot_type, ps.status, ps.vehicle_number,
               ps.vehicle_type, ps.booking_time, ps.parking_fee,
               pa.area_name
        FROM parking_slot ps
        JOIN parking_area pa ON ps.area_id = pa.area_id
        WHERE 1 = 1
    """
    params = []

    if vehicle_search:
        query += " AND ps.vehicle_number LIKE %s"
        params.append(f"%{vehicle_search}%")

    if zone_filter:
        query += " AND pa.area_name = %s"
        params.append(zone_filter)

    cursor.execute(query, params)
    slots = cursor.fetchall()

    cursor.execute("SELECT area_name FROM parking_area")
    zones = cursor.fetchall()

    conn.close()
    return render_template("dashboard.html", slots=slots, zones=zones)


@app.route('/book_slot', methods=['POST'])
def book_slot():
    slot_id = request.form['slot_id']
    vehicle_number = request.form['vehicle_number']
    vehicle_type = request.form['vehicle_type']
    user_id = session['user_id']

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE parking_slot
        SET status='occupied', vehicle_number=%s, vehicle_type=%s, booking_time=NOW()
        WHERE slot_id=%s
    """, (vehicle_number, vehicle_type, slot_id))

    cursor.execute("""
        INSERT INTO booking (user_id, slot_id, booking_date, in_time, status)
        VALUES (%s, %s, CURDATE(), NOW(), 'active')
    """, (user_id, slot_id))

    conn.commit()
    conn.close()
    return redirect('/dashboard')


@app.route('/checkout_slot', methods=['POST'])
def checkout_slot():
    if session.get("role") != "admin":  # 🔥 Only admin can checkout
        flash("Access Denied! Only admin can checkout vehicles.")
        return redirect("/dashboard")

    slot_id = request.form['slot_id']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT booking_id, in_time
        FROM booking
        WHERE slot_id=%s AND status='active'
        ORDER BY booking_id DESC LIMIT 1
    """, (slot_id,))
    booking = cursor.fetchone()

    if booking:
        booking_id = booking['booking_id']
        in_time = booking['in_time']

        cursor.execute("SELECT TIMESTAMPDIFF(MINUTE, %s, NOW()) AS mins", (in_time,))
        mins = cursor.fetchone()['mins']
        parking_fee = max(20, mins * 2)

        cursor.execute("""
            UPDATE booking
            SET out_time = NOW(), status='completed'
            WHERE booking_id=%s
        """, (booking_id,))

        cursor.execute("""
            UPDATE parking_slot
            SET status='available', vehicle_number=NULL,
                vehicle_type=NULL, parking_fee=%s, booking_time=NULL
            WHERE slot_id=%s
        """, (parking_fee, slot_id))

        conn.commit()

    conn.close()
    return redirect('/dashboard')


@app.route('/history')
def history():
    if session.get("role") != "admin":  # 🔥 Only admin can see booking history
        flash("Access Denied! Only admin can view booking history.")
        return redirect("/dashboard")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.booking_id, b.booking_date, b.in_time, b.out_time, b.status,
               p.slot_number, p.area_id, b.user_id
        FROM booking b
        JOIN parking_slot p ON b.slot_id = p.slot_id
    """)
    history = cursor.fetchall()
    conn.close()
    return render_template('history.html', history=history)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
