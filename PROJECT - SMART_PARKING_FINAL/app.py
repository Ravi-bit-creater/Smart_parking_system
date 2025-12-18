from flask import Flask, render_template, request, redirect, flash, session, jsonify
from config import get_connection
import pymysql
from datetime import datetime, timedelta
import qrcode
import io
import base64
import random
import string

app = Flask(__name__)
app.secret_key = "my_super_secret_key_123"

# Vehicle pricing configuration (per minute rates)
VEHICLE_RATES = {
    'Car': 3,       # ₹3 per minute for cars
    'SUV': 4,       # ₹4 per minute for SUVs
    'Truck': 5,     # ₹5 per minute for trucks
    'Bike': 1,      # ₹1 per minute for bikes
    'Scooter': 1,   # ₹1 per minute for scooters
    'Two Wheeler': 1, # ₹1 per minute for two wheelers
    'Four Wheeler': 3, # ₹3 per minute for four wheelers
}

# Minimum parking fees
MINIMUM_FEES = {
    'Car': 30,      # Minimum ₹30 for cars
    'SUV': 40,      # Minimum ₹40 for SUVs
    'Truck': 50,    # Minimum ₹50 for trucks
    'Bike': 10,     # Minimum ₹10 for bikes
    'Scooter': 10,  # Minimum ₹10 for scooters
    'Two Wheeler': 10, # Minimum ₹10 for two wheelers
    'Four Wheeler': 30, # Minimum ₹30 for four wheelers
}

# Helper function for vehicle icons
def get_vehicle_icon(vehicle_type):
    """Helper function to get Font Awesome icon for vehicle type."""
    if not vehicle_type or str(vehicle_type).lower() in ['na', 'n/a', 'null', 'none']:
        return "fa-question-circle"
    
    vehicle_type_lower = str(vehicle_type).lower()
    
    if 'car' in vehicle_type_lower:
        return "fa-car"
    elif 'suv' in vehicle_type_lower:
        return "fa-shuttle-van"
    elif 'truck' in vehicle_type_lower:
        return "fa-truck"
    elif 'bike' in vehicle_type_lower or 'motorcycle' in vehicle_type_lower:
        return "fa-motorcycle"
    elif 'scooter' in vehicle_type_lower:
        return "fa-motorcycle"
    elif 'two wheeler' in vehicle_type_lower:
        return "fa-motorcycle"
    elif 'four wheeler' in vehicle_type_lower:
        return "fa-car"
    else:
        return "fa-question-circle"

# Make it available to all templates
@app.context_processor
def utility_processor():
    return dict(get_vehicle_icon=get_vehicle_icon)

def calculate_parking_fee(vehicle_type, minutes_parked):
    """Calculate parking fee based on vehicle type and time"""
    if not vehicle_type or str(vehicle_type).lower() in ['na', 'n/a', 'null', 'none']:
        # Default rate if vehicle type is not specified
        rate = 2
        minimum = 20
    else:
        rate = VEHICLE_RATES.get(vehicle_type, 2)  # Default ₹2 per minute
        minimum = MINIMUM_FEES.get(vehicle_type, 20)  # Default minimum ₹20
    
    # Calculate fee: rate per minute * minutes
    calculated_fee = rate * minutes_parked
    
    # Apply minimum fee
    final_fee = max(calculated_fee, minimum)
    
    return round(final_fee, 2)

def generate_transaction_id():
    """Generate a unique transaction ID for payments"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"TXN{timestamp}{random_str}"

def generate_qr_code(data):
    """Generate QR code for UPI payment"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

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

        # Check if email already exists
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        if cursor.fetchone():
            flash("Email already registered! Please use a different email.")
            conn.close()
            return redirect('/register')

        insert_query = """
            INSERT INTO user (name, email, password, role) 
            VALUES (%s, %s, %s, 'user')
        """
        cursor.execute(insert_query, (name, email, password))
        conn.commit()
        conn.close()

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
        conn.close()

        if user:
            session['user_name'] = user['name']
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            flash("Login Successful!")
            
            if user['role'] == 'admin':
                return redirect('/dashboard')
            else:
                return redirect('/user_dashboard')
        else:
            flash("Invalid email or password!")
            return redirect('/login')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect('/login')
    
    if session.get('role') != 'admin':
        flash("Access Denied! Admin only area.")
        return redirect('/user_dashboard')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    vehicle_search = request.args.get('vehicle_search')
    zone_filter = request.args.get('zone_filter')

    query = """
        SELECT ps.slot_id, ps.slot_number, ps.slot_type, ps.status, ps.vehicle_number,
               ps.vehicle_type, ps.booking_time, ps.parking_fee,
               pa.area_name, pa.area_id
        FROM parking_slot ps
        JOIN parking_area pa ON ps.area_id = pa.area_id
        WHERE 1 = 1
    """
    params = []

    if vehicle_search:
        query += " AND ps.vehicle_number LIKE %s"
        params.append(f"%{vehicle_search}%")

    if zone_filter:
        query += " AND pa.area_id = %s"
        params.append(zone_filter)

    cursor.execute(query, params)
    slots = cursor.fetchall()

    cursor.execute("SELECT area_id, area_name FROM parking_area")
    zones = cursor.fetchall()

    # Calculate statistics
    cursor.execute("SELECT COUNT(*) as total FROM parking_slot")
    total_slots = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as available FROM parking_slot WHERE status = 'available'")
    available_slots = cursor.fetchone()['available']
    
    cursor.execute("SELECT COUNT(*) as occupied FROM parking_slot WHERE status = 'occupied'")
    occupied_slots = cursor.fetchone()['occupied']
    
    # Calculate total revenue from all checked out bookings
    cursor.execute("""
        SELECT COALESCE(SUM(ps.parking_fee), 0) as total_revenue 
        FROM parking_slot ps 
        WHERE ps.parking_fee > 0
    """)
    total_revenue = cursor.fetchone()['total_revenue'] or 0

    conn.close()
    return render_template("dashboard.html", slots=slots, zones=zones, 
                          total_slots=total_slots, available_slots=available_slots,
                          occupied_slots=occupied_slots, total_revenue=total_revenue)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect('/login')
    
    user_id = session['user_id']
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get user's current booking with better vehicle type handling
    cursor.execute("""
        SELECT b.*, ps.slot_number, pa.area_name, 
               COALESCE(b.vehicle_type, ps.vehicle_type) as vehicle_type, 
               ps.vehicle_number
        FROM booking b
        JOIN parking_slot ps ON b.slot_id = ps.slot_id
        JOIN parking_area pa ON ps.area_id = pa.area_id
        WHERE b.user_id = %s AND b.status = 'checkedin'
        ORDER BY b.booking_id DESC LIMIT 1
    """, (user_id,))
    current_booking = cursor.fetchone()

    # Get user's booking history with proper vehicle type and fee
    cursor.execute("""
        SELECT b.*, ps.slot_number, pa.area_name, 
               COALESCE(b.vehicle_type, ps.vehicle_type) as vehicle_type,
               ps.vehicle_number,
               COALESCE(ps.parking_fee, 0) as parking_fee
        FROM booking b
        JOIN parking_slot ps ON b.slot_id = ps.slot_id
        JOIN parking_area pa ON ps.area_id = pa.area_id
        WHERE b.user_id = %s
        ORDER BY b.booking_id DESC
    """, (user_id,))
    user_history = cursor.fetchall()

    # Get available slots
    cursor.execute("""
        SELECT ps.slot_id, ps.slot_number, ps.slot_type, pa.area_name
        FROM parking_slot ps
        JOIN parking_area pa ON ps.area_id = pa.area_id
        WHERE ps.status = 'available'
    """)
    available_slots = cursor.fetchall()

    conn.close()
    return render_template("user_dashboard.html", 
                          current_booking=current_booking,
                          user_history=user_history,
                          available_slots=available_slots)

@app.route('/book_slot', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect('/login')
    
    slot_id = request.form['slot_id']
    vehicle_number = request.form['vehicle_number']
    vehicle_type = request.form['vehicle_type']
    user_id = session['user_id']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if slot is still available
        cursor.execute("SELECT status FROM parking_slot WHERE slot_id = %s", (slot_id,))
        slot_status = cursor.fetchone()
        
        if not slot_status or slot_status[0] != 'available':
            flash("Slot is no longer available!")
            conn.close()
            return redirect('/user_dashboard')

        # Update parking slot status
        cursor.execute("""
            UPDATE parking_slot
            SET status='occupied', vehicle_number=%s, vehicle_type=%s, 
                booking_time=NOW(), parking_fee=0
            WHERE slot_id=%s
        """, (vehicle_number, vehicle_type, slot_id))

        # Ensure vehicle_type column exists in booking table
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'booking' 
                AND COLUMN_NAME = 'vehicle_type'
            """)
            if cursor.fetchone()[0] == 0:
                cursor.execute("ALTER TABLE booking ADD COLUMN vehicle_type VARCHAR(50) DEFAULT NULL")
                conn.commit()
        except Exception as col_error:
            print(f"Column check failed: {col_error}")

        # Create booking record with vehicle_type
        cursor.execute("""
            INSERT INTO booking (user_id, slot_id, booking_date, in_time, status, vehicle_type)
            VALUES (%s, %s, CURDATE(), NOW(), 'checkedin', %s)
        """, (user_id, slot_id, vehicle_type))

        conn.commit()
        flash("Slot booked successfully! Your vehicle is now checked in.")
        
    except Exception as e:
        conn.rollback()
        flash(f"Error booking slot: {str(e)}")
        print(f"Booking error details: {str(e)}")
    
    finally:
        conn.close()
    
    return redirect('/user_dashboard')

@app.route('/checkout_slot', methods=['POST'])
def checkout_slot():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect('/login')
    
    if session.get("role") != "admin":
        flash("Access Denied! Only admin can checkout vehicles.")
        return redirect("/dashboard")

    slot_id = request.form['slot_id']
    payment_method = request.form.get('payment_method', 'cash')  # Default to cash

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get active booking for this slot with vehicle type
        cursor.execute("""
            SELECT b.booking_id, b.in_time, 
                   COALESCE(b.vehicle_type, ps.vehicle_type) as vehicle_type,
                   ps.vehicle_number, ps.slot_number, pa.area_name
            FROM booking b
            JOIN parking_slot ps ON b.slot_id = ps.slot_id
            JOIN parking_area pa ON ps.area_id = pa.area_id
            WHERE b.slot_id=%s AND b.status='checkedin'
            ORDER BY b.booking_id DESC LIMIT 1
        """, (slot_id,))
        booking = cursor.fetchone()

        if booking:
            booking_id = booking['booking_id']
            in_time = booking['in_time']
            vehicle_type = booking['vehicle_type']
            vehicle_number = booking['vehicle_number']
            slot_number = booking['slot_number']
            area_name = booking['area_name']
            
            # Clean up vehicle type string
            if vehicle_type and str(vehicle_type).lower() in ['na', 'n/a', 'null', 'none']:
                vehicle_type = 'Car'  # Default to Car
            
            # Calculate parking duration in minutes
            cursor.execute("SELECT TIMESTAMPDIFF(MINUTE, %s, NOW()) AS mins", (in_time,))
            result = cursor.fetchone()
            mins = result['mins'] if result and result['mins'] else 1  # Minimum 1 minute
            
            # Calculate parking fee based on vehicle type
            parking_fee = calculate_parking_fee(vehicle_type, mins)
            
            # Generate transaction ID
            transaction_id = generate_transaction_id()
            
            # Generate QR code for UPI if payment method is QR
            qr_code_base64 = None
            upi_id = "rathinam.parking@upi"  # Your UPI ID
            upi_url = f"upi://pay?pa={upi_id}&pn=Rathinam%20Parking&am={parking_fee}&tn=Parking%20Fee%20{transaction_id}"
            
            if payment_method == 'qr':
                qr_code_base64 = generate_qr_code(upi_url)
            
            # Update booking as checked out with payment info
            cursor.execute("""
                UPDATE booking
                SET out_time = NOW(), status='checkedout', 
                    payment_method=%s, transaction_id=%s
                WHERE booking_id=%s
            """, (payment_method, transaction_id, booking_id))

            # Free up the parking slot and store the fee
            cursor.execute("""
                UPDATE parking_slot
                SET status='available', vehicle_number=NULL,
                    vehicle_type=NULL, parking_fee=%s, booking_time=NULL
                WHERE slot_id=%s
            """, (parking_fee, slot_id))

            conn.commit()
            
            # Store payment info in session for receipt
            session['last_checkout'] = {
                'slot_number': slot_number,
                'area_name': area_name,
                'vehicle_number': vehicle_number,
                'vehicle_type': vehicle_type,
                'in_time': in_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(in_time, datetime) else str(in_time),
                'out_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'minutes': mins,
                'parking_fee': parking_fee,
                'payment_method': payment_method,
                'transaction_id': transaction_id,
                'upi_url': upi_url,
                'qr_code': qr_code_base64
            }
            
            return redirect('/checkout_receipt')
        else:
            flash("No active booking found for this slot!")

    except Exception as e:
        conn.rollback()
        flash(f"Error during checkout: {str(e)}")
        print(f"Checkout error details: {str(e)}")
    
    finally:
        conn.close()
    
    return redirect('/dashboard')

@app.route('/checkout_receipt')
def checkout_receipt():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access Denied!")
        return redirect('/dashboard')
    
    checkout_data = session.get('last_checkout')
    if not checkout_data:
        flash("No checkout information found!")
        return redirect('/dashboard')
    
    return render_template('checkout_receipt.html', checkout=checkout_data)

@app.route('/history')
def history():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect('/login')
    
    if session.get("role") != "admin":
        flash("Access Denied! Only admin can view all booking history.")
        return redirect("/user_dashboard")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get complete booking history with all details
    # Clean up vehicle_type to handle 'na', 'N/A', None values
    cursor.execute("""
        SELECT 
            b.booking_id,
            b.booking_date,
            b.in_time,
            b.out_time,
            b.status,
            b.payment_method,
            b.transaction_id,
            CASE 
                WHEN COALESCE(b.vehicle_type, ps.vehicle_type) IN ('na', 'N/A', 'null', 'NULL', '') 
                THEN NULL
                ELSE COALESCE(b.vehicle_type, ps.vehicle_type)
            END as vehicle_type,
            ps.slot_number,
            ps.area_id,
            b.user_id,
            ps.vehicle_number,
            COALESCE(ps.parking_fee, 0) as parking_fee,
            u.name as user_name
        FROM booking b
        JOIN parking_slot ps ON b.slot_id = ps.slot_id
        JOIN user u ON b.user_id = u.user_id
        ORDER BY b.booking_date DESC, b.in_time DESC
    """)
    history = cursor.fetchall()
    
    # Clean up the history data for display
    for booking in history:
        # Clean vehicle type for display
        if booking['vehicle_type'] and str(booking['vehicle_type']).lower() in ['na', 'n/a', 'null', 'none', '']:
            booking['vehicle_type'] = None
        
        # Ensure parking_fee is numeric
        if booking['parking_fee'] is None:
            booking['parking_fee'] = 0
    
    # Calculate statistics
    active_count = sum(1 for booking in history if booking['status'] == 'checkedin')
    completed_count = sum(1 for booking in history if booking['status'] == 'checkedout')
    cancelled_count = sum(1 for booking in history if booking['status'] == 'cancelled')
    total_count = len(history)
    
    conn.close()
    
    return render_template('history.html', 
                         history=history,
                         active_count=active_count,
                         completed_count=completed_count,
                         cancelled_count=cancelled_count,
                         total_count=total_count)

@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'user_id' not in session:
        flash("Please login first!")
        return redirect('/login')
    
    booking_id = request.form['booking_id']
    user_id = session['user_id']
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get booking details
        cursor.execute("""
            SELECT b.*, ps.slot_id, COALESCE(b.vehicle_type, ps.vehicle_type) as vehicle_type
            FROM booking b
            JOIN parking_slot ps ON b.slot_id = ps.slot_id
            WHERE b.booking_id = %s AND b.user_id = %s
        """, (booking_id, user_id))
        booking = cursor.fetchone()
        
        if not booking:
            flash("Booking not found or access denied!")
            return redirect('/user_dashboard')
        
        if booking['status'] != 'checkedin':
            flash("Only active bookings can be cancelled!")
            return redirect('/user_dashboard')
        
        # Update booking status
        cursor.execute("""
            UPDATE booking 
            SET status = 'cancelled', out_time = NOW()
            WHERE booking_id = %s
        """, (booking_id,))
        
        # Free up the parking slot
        cursor.execute("""
            UPDATE parking_slot
            SET status = 'available', 
                vehicle_number = NULL,
                vehicle_type = NULL,
                booking_time = NULL,
                parking_fee = 0
            WHERE slot_id = %s
        """, (booking['slot_id'],))
        
        conn.commit()
        flash("Booking cancelled successfully!")
        
    except Exception as e:
        conn.rollback()
        flash(f"Error cancelling booking: {str(e)}")
    
    finally:
        conn.close()
    
    return redirect('/user_dashboard')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect('/login')

# Database initialization route
@app.route('/init-db')
def init_db():
    if 'user_id' not in session or session.get('role') != 'admin':
        return "Access denied", 403
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if payment columns exist in booking table
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'booking' 
            AND COLUMN_NAME = 'payment_method'
        """)
        if cursor.fetchone()[0] == 0:
            # Add payment columns
            cursor.execute("""
                ALTER TABLE booking 
                ADD COLUMN payment_method VARCHAR(20) DEFAULT 'cash',
                ADD COLUMN transaction_id VARCHAR(50) DEFAULT NULL
            """)
            conn.commit()
            return "Database updated: Added payment columns to booking table"
        else:
            return "Database already has payment columns"
            
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)