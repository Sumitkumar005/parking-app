from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Handle both local SQLite and production PostgreSQL
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Production: Use PostgreSQL (fix postgres:// to postgresql://)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Development: Use SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///db.sqlite3')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

class Lot(db.Model):
    __tablename__ = 'lot'
    lot_id = db.Column(db.Integer, primary_key=True)
    prime_loc = db.Column(db.String(30), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    price_per_hr = db.Column(db.Float, nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)
    is_shaded = db.Column(db.Boolean, default=False)

class Spot(db.Model):
    __tablename__ = 'spot'
    spot_id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('lot.lot_id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(1), nullable=False, default='a')

class Reserve(db.Model):
    __tablename__ = 'reserve'
    reserve_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('lot.lot_id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('spot.spot_id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now)
    end_time = db.Column(db.DateTime, nullable=True)
    price_per_hr = db.Column(db.Float, nullable=False)
    vehicle_num = db.Column(db.String(15), nullable=False)
    is_ongoing = db.Column(db.Boolean, nullable=False, default=True)

class Payment(db.Model):
    __tablename__ = 'payment'
    payment_id = db.Column(db.Integer, primary_key=True)
    reserve_id = db.Column(db.Integer, db.ForeignKey('reserve.reserve_id'), nullable=False)
    total_amt = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String, nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)

# Decorators
def auth_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login first", "warning")
            return redirect(url_for('login'))
    return inner

def admin_required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first", "warning")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user:
            return redirect(url_for('logout'))
        if user.is_admin == False:
            flash("You are not allowed to access this page", "warning")
            return redirect(url_for('home'))
        return func(*args, **kwargs)
    return inner

# Routes
@app.route('/')
@app.route('/home')
@auth_required
def home():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    if user.is_admin:
        return redirect(url_for('admin'))
    
    lots = Lot.query.all()
    current = Reserve.query.filter_by(user_id=user.user_id, is_ongoing=True).all()
    
    # Add spots data to lots for template
    lots_with_spots = []
    for lot in lots:
        spots = Spot.query.filter_by(lot_id=lot.lot_id).all()
        lot.spots = spots  # Add spots to lot object
        lots_with_spots.append(lot)
    
    return render_template("user/user_dashboard.html", lots=lots_with_spots, current=current)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash("Already logged in")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        print(f"Login attempt - Email: {email}, Password: {password}")  # Debug

        if email and password:
            user = User.query.filter_by(email=email).first()
            print(f"User found: {user}")  # Debug
            
            if user:
                print(f"User is_admin: {user.is_admin}")  # Debug
                password_check = check_password_hash(user.password, password)
                print(f"Password check result: {password_check}")  # Debug
                
                if password_check:
                    flash("Login successful", "success")
                    session['user_id'] = user.user_id
                    print(f"Session set for user_id: {user.user_id}")  # Debug
                    return redirect(url_for('home'))
                else:
                    flash("Incorrect password. Please try again", "error")
            else:
                flash("Account with this email does not exist. Try again or create account", "error")
        else:
            flash("Please fill all fields", "warning")

    return render_template("login.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if 'user_id' in session:
        flash("Already logged in")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        
        print(f"Registration attempt - Email: {email}, Name: {name}")  # Debug

        if not email or not name or not password1 or not password2:
            flash("Please fill all fields", "warning")
            return render_template("signup.html")
        
        if len(password1) < 8:
            flash("Password must be at least 8 characters long", "error")
            return render_template("signup.html")
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash("An account with this email already exists", "error")
        elif password1 != password2:
            flash("Passwords do not match", "error")
        else:
            try:
                new_user = User(email=email, password=generate_password_hash(password1), name=name)
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.user_id
                print(f"User created successfully: {new_user.user_id}")  # Debug
                flash("Welcome, " + new_user.name + "!", "success")
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                print(f"Registration error: {str(e)}")  # Debug
                flash("Registration failed. Please try again.", "error")
                return render_template("signup.html")
        
    return render_template("signup.html")

@app.route('/logout')
def logout():
    if 'user_id' in session:
        session.pop('user_id')
        flash("You have been logged out", "success")
    else:
        flash("You are already logged out", "warning")
    
    return redirect(url_for('login'))

@app.route('/debug-admin')
def debug_admin():
    """Debug route to check admin user - REMOVE IN PRODUCTION"""
    admin = User.query.filter_by(email='admin@nicmar.ac.in').first()
    all_users = User.query.all()
    
    result = f"Total users in database: {len(all_users)}<br><br>"
    
    if admin:
        result += f"Admin exists: Email={admin.email}, Name={admin.name}, is_admin={admin.is_admin}, user_id={admin.user_id}<br><br>"
    else:
        result += "Admin user not found!<br><br>"
    
    result += "All users:<br>"
    for user in all_users:
        result += f"- {user.email} (Admin: {user.is_admin})<br>"
    
    return result

@app.route('/create-admin-now')
def create_admin_now():
    """Emergency admin creation route"""
    try:
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@nicmar.ac.in').first()
        if existing_admin:
            return f"Admin already exists! Email: {existing_admin.email}, Admin: {existing_admin.is_admin}"
        
        # Create new admin
        passhash = generate_password_hash('nicmar2024')
        new_admin = User(email='admin@nicmar.ac.in', password=passhash, name='NICMAR Admin', is_admin=True)
        db.session.add(new_admin)
        db.session.commit()
        
        return "Admin user created successfully! Email: admin@nicmar.ac.in, Password: nicmar2024"
    except Exception as e:
        db.session.rollback()
        return f"Error creating admin: {str(e)}"

@app.route('/make-user-admin/<email>')
def make_user_admin(email):
    """Make any existing user an admin"""
    try:
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_admin = True
            db.session.commit()
            return f"User {email} is now an admin!"
        else:
            return f"User {email} not found!"
    except Exception as e:
        db.session.rollback()
        return f"Error: {str(e)}"

@app.route('/debug-db')
def debug_db():
    """Debug route to check database status"""
    try:
        user_count = User.query.count()
        lot_count = Lot.query.count()
        spot_count = Spot.query.count()
        
        return f"""
        Database Status:<br>
        Users: {user_count}<br>
        Lots: {lot_count}<br>
        Spots: {spot_count}<br>
        Database connection: OK
        """
    except Exception as e:
        return f"Database error: {str(e)}"

@app.route('/profile', methods=['GET', 'POST'])
@auth_required
def profile():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        name = request.form.get('name')
        cpass = request.form.get('cpassword')
        pass1 = request.form.get('password1')
        pass2 = request.form.get('password2')

        if name and cpass and pass1 and pass2:
            if check_password_hash(user.password, cpass):
                if len(pass1) < 8:
                    flash("Password must be at least 8 characters long", "error")
                    return render_template('profile.html', user=user)
                
                if pass1 == pass2:
                    user.name = name
                    user.password = generate_password_hash(pass1)
                    db.session.commit()
                    flash("Successfully updated password", "success")
                    return redirect(url_for('profile'))
                else:
                    flash("Passwords do not match", "error")
            else:
                flash("Incorrect password", "error")
        else:
            flash("Please fill all details", "warning")  
            
    return render_template('profile.html', user=user)

@app.route('/admin')
@admin_required
def admin():
    lots = Lot.query.all()
    return render_template("admin/admin_dashboard.html", lots=lots)

@app.route('/admin/users')
@admin_required
def view_users():
    users = User.query.all()
    return render_template("admin/view_users.html", users=users)

@app.route('/admin/view-parking-records')
@admin_required
def admin_view_parking():
    records = Reserve.query.all()
    return render_template("admin/admin_summary.html", records=records)

@app.route('/admin-stats')
@admin_required
def admin_stats():
    total_spots = Spot.query.count()
    occupied = Spot.query.filter_by(status='o').count()
    vacant = total_spots - occupied
    return render_template("admin/admin_chart.html", occupied=occupied, vacant=vacant)

@app.route('/admin/lot/add-lot', methods=['GET', 'POST'])
@admin_required
def add_lot():
    if request.method == "POST":
        prime_loc = request.form.get('prime_loc')
        address = request.form.get('address')
        pin = request.form.get('pin')
        max_spots = request.form.get('max_spots')
        price = request.form.get('price')
        is_shaded = 'is_shaded' in request.form

        if prime_loc and address and pin and max_spots and price:
            if is_shaded:
                new_lot = Lot(prime_loc=prime_loc, address=address, pincode=pin, max_spots=max_spots, price_per_hr=price, is_shaded=True)
            else:
                new_lot = Lot(prime_loc=prime_loc, address=address, pincode=pin, max_spots=max_spots, price_per_hr=price)
            db.session.add(new_lot)
            db.session.flush()

            for i in range(int(max_spots)):
                new_spot = Spot(lot_id=new_lot.lot_id)
                db.session.add(new_spot)

            db.session.commit()
            flash("Parking lot created successfully!", "success")
            return redirect(url_for("admin"))
        
        flash("Please fill out all fields", "warning")

    return render_template("admin/new_lot.html")

@app.route('/lot/<int:lot_id>')
@auth_required
def view_lot(lot_id):
    lot = Lot.query.get(lot_id)
    if lot:
        # Get available spots count
        total_spots = Spot.query.filter_by(lot_id=lot_id).count()
        occupied_spots = Spot.query.filter_by(lot_id=lot_id, status='o').count()
        available_spots = total_spots - occupied_spots
        
        return render_template("view_lot.html", lot=lot, available_spots=available_spots, total_spots=total_spots)
    else:
        flash("Lot not found", "error")
        return redirect(url_for('home'))

@app.route('/book-spot/<int:lot_id>', methods=['GET', 'POST'])
@auth_required
def book_spot(lot_id):
    lot = Lot.query.get(lot_id)
    if not lot:
        flash("Parking lot not found", "error")
        return redirect(url_for('home'))
    
    user = User.query.get(session['user_id'])
    
    # Check if user already has an ongoing reservation
    existing_reservation = Reserve.query.filter_by(user_id=session['user_id'], is_ongoing=True).first()
    if existing_reservation:
        flash("You already have an active parking reservation", "warning")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        vehicle_num = request.form.get('vno')  # Template uses 'vno' as field name
        if not vehicle_num:
            flash("Please enter vehicle number", "warning")
            # Find an available spot to show in template
            available_spot = Spot.query.filter_by(lot_id=lot_id, status='a').first()
            return render_template("user/book_spot.html", lot=lot, user=user, spot=available_spot)
        
        # Find available spot
        available_spot = Spot.query.filter_by(lot_id=lot_id, status='a').first()
        if not available_spot:
            flash("No parking spots available", "error")
            return redirect(url_for('home'))
        
        # Create reservation
        try:
            reservation = Reserve(
                user_id=session['user_id'],
                lot_id=lot_id,
                spot_id=available_spot.spot_id,
                price_per_hr=lot.price_per_hr,
                vehicle_num=vehicle_num,
                start_time=datetime.now()
            )
            
            # Mark spot as occupied
            available_spot.status = 'o'
            
            db.session.add(reservation)
            db.session.commit()
            
            flash(f"Parking spot booked successfully! Spot #{available_spot.spot_id}", "success")
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash("Error booking parking spot. Please try again.", "error")
            available_spot = Spot.query.filter_by(lot_id=lot_id, status='a').first()
            return render_template("user/book_spot.html", lot=lot, user=user, spot=available_spot)
    
    # Check available spots
    available_spot = Spot.query.filter_by(lot_id=lot_id, status='a').first()
    if not available_spot:
        flash("No parking spots available in this lot", "error")
        return redirect(url_for('home'))
    
    return render_template("user/book_spot.html", lot=lot, user=user, spot=available_spot)

@app.route('/release-spot/<int:reserve_id>')
@auth_required
def release_spot(reserve_id):
    reservation = Reserve.query.get(reserve_id)
    if not reservation or reservation.user_id != session['user_id']:
        flash("Reservation not found", "error")
        return redirect(url_for('home'))
    
    if not reservation.is_ongoing:
        flash("This reservation is already completed", "warning")
        return redirect(url_for('home'))
    
    try:
        # Calculate duration and cost
        end_time = datetime.now()
        duration = end_time - reservation.start_time
        hours = duration.total_seconds() / 3600
        total_cost = hours * reservation.price_per_hr
        
        # Update reservation
        reservation.end_time = end_time
        reservation.is_ongoing = False
        
        # Free up the spot
        spot = Spot.query.get(reservation.spot_id)
        if spot:
            spot.status = 'a'
        
        # Create payment record
        payment = Payment(
            reserve_id=reservation.reserve_id,
            total_amt=total_cost,
            payment_method='Cash',
            transaction_date=end_time
        )
        
        db.session.add(payment)
        db.session.commit()
        
        flash(f"Parking released successfully! Total cost: ₹{total_cost:.2f}", "success")
        
    except Exception as e:
        db.session.rollback()
        flash("Error releasing parking spot. Please try again.", "error")
    
    return redirect(url_for('home'))

@app.route('/user/summary')
@auth_required
def view_summary():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    
    # Get user's reservation history
    reservations = Reserve.query.filter_by(user_id=user.user_id).all()
    
    # Get payment history
    payments = []
    for reservation in reservations:
        payment = Payment.query.filter_by(reserve_id=reservation.reserve_id).first()
        if payment:
            payments.append({
                'reservation': reservation,
                'payment': payment,
                'lot': Lot.query.get(reservation.lot_id)
            })
    
    return render_template("user/user_summary.html", reservations=reservations, payments=payments)

@app.route('/user/history')
@auth_required
def transaction_history():
    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('logout'))
    
    # Get all completed reservations with payments
    completed_reservations = Reserve.query.filter_by(user_id=user.user_id, is_ongoing=False).all()
    
    history = []
    for reservation in completed_reservations:
        payment = Payment.query.filter_by(reserve_id=reservation.reserve_id).first()
        lot = Lot.query.get(reservation.lot_id)
        
        if payment and lot:
            history.append({
                'reservation': reservation,
                'payment': payment,
                'lot': lot
            })
    
    return render_template("user/transaction_history.html", history=history)

@app.route('/admin/lot/<int:lot_id>/edit-lot', methods=['GET', 'POST'])
@admin_required
def edit_lot(lot_id):
    lot = Lot.query.get(lot_id)
    if lot:
        if request.method == "POST":
            prime_loc = request.form.get('prime_loc')
            address = request.form.get('address')
            pin = request.form.get('pin')
            max_spots = request.form.get('max_spots')
            price = request.form.get('price')
            is_shaded = 'is_shaded' in request.form

            if prime_loc and address and pin and max_spots and price:
                lot.prime_loc = prime_loc
                lot.address = address
                lot.pincode = pin
                lot.max_spots = max_spots
                lot.price_per_hr = price
                lot.is_shaded = is_shaded
                
                # Handle spot count changes
                spots_before = Spot.query.filter_by(lot_id=lot_id).all()
                max_before = len(spots_before)
                if int(max_spots) > max_before:
                    for i in range(int(max_spots) - max_before):
                        new_spot = Spot(lot_id=lot_id)
                        db.session.add(new_spot)
                elif int(max_spots) < max_before:
                    for spot in spots_before[int(max_spots):]:
                        db.session.delete(spot)
                
                db.session.commit()
                flash("Parking lot details updated successfully!", "success")
                return redirect(url_for("admin"))
        
            flash("Please fill out all fields", "warning")
    else:
        flash("Lot not found", "error")
        return redirect(url_for('admin'))

    return render_template("admin/edit_lot.html", lot=lot)

@app.route('/admin/lot/<int:lot_id>/delete-lot')
@admin_required
def delete_lot(lot_id):
    lot = Lot.query.get(lot_id)
    if lot:
        reservation = Reserve.query.filter_by(lot_id=lot_id, is_ongoing=True).first()
        if reservation:
            flash("Cannot delete a lot that has been occupied", "error")
            return redirect(url_for('admin'))
        
        db.session.delete(lot)
        db.session.commit()
        flash("Lot #" + str(lot_id) + " deleted successfully!", "success")
        return redirect(url_for('admin'))
    else:
        flash("Lot not found", "error")
    return redirect(url_for('admin'))

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create admin user if doesn't exist - More robust approach
    try:
        admin = User.query.filter_by(email='admin@nicmar.ac.in').first()
        if not admin:
            print("Creating admin user...")
            passhash = generate_password_hash('nicmar2024')
            admin = User(email='admin@nicmar.ac.in', password=passhash, name='NICMAR Admin', is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists")
            # Ensure admin flag is set
            if not admin.is_admin:
                admin.is_admin = True
                db.session.commit()
                print("Admin flag updated")
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.session.rollback()
    
    # Create sample parking lots if none exist
    if Lot.query.count() == 0:
        # NICMAR Main Campus Lot
        sample_lot1 = Lot(
            prime_loc='NICMAR Main Campus',
            address='NICMAR University, Pune-Bangalore Highway',
            pincode='411045',
            price_per_hr=15.0,
            max_spots=50,
            is_shaded=True
        )
        db.session.add(sample_lot1)
        db.session.flush()
        
        # Create spots for sample lot 1
        for i in range(50):
            spot = Spot(lot_id=sample_lot1.lot_id)
            db.session.add(spot)
        
        # NICMAR Hostel Parking
        sample_lot2 = Lot(
            prime_loc='NICMAR Hostel Area',
            address='NICMAR Hostel Complex, Pune',
            pincode='411045',
            price_per_hr=10.0,
            max_spots=30,
            is_shaded=False
        )
        db.session.add(sample_lot2)
        db.session.flush()
        
        # Create spots for sample lot 2
        for i in range(30):
            spot = Spot(lot_id=sample_lot2.lot_id)
            db.session.add(spot)
            
        db.session.commit()
        print("Sample parking lots created successfully!")

if __name__ == "__main__":
    # Production vs Development configuration
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if not is_production:
        print("Available routes:")
        for rule in app.url_map.iter_rules():
            print(f"  {rule.endpoint}: {rule.rule}")
    
    # Use PORT environment variable for production deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=not is_production)