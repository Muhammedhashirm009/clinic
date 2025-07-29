import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from models import db, User, Patient, Treatment, SystemStats
# Firebase imports will be enabled once packages are installed
# from firebase_config import firebase_config
# from firebase_models import FirebaseUser, FirebasePatient, FirebaseTreatment, generate_patient_id as firebase_generate_patient_id
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration with fallback to SQLite
database_url = os.environ.get("DATABASE_URL")
if not database_url or "ep-wild-firefly-a56pariz.us-east-2.aws.neon.tech" in database_url:
    # Use SQLite fallback if PostgreSQL is not available
    database_url = "sqlite:///patient_management.db"
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {}
else:
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions
def role_required(role):
    """Decorator to check if user has required role"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role != role:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def generate_patient_id():
    """Generate unique patient ID"""
    import random
    import string
    while True:
        # Generate format: PT2024001, PT2024002, etc.
        year = datetime.now().year
        random_num = random.randint(1000, 9999)
        patient_id = f"PT{year}{random_num}"
        
        # Check if ID already exists
        if not Patient.query.filter_by(patient_id=patient_id).first():
            return patient_id

# Authentication routes
@app.route('/')
def index():
    """Main page - redirect to login or dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            
            # Redirect to intended page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Dashboard routes
@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard for all users"""
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    elif current_user.role == 'receptionist':
        return redirect(url_for('receptionist_dashboard'))
    else:
        flash('Unknown user role.', 'error')
        return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    """Admin dashboard with system statistics"""
    # Get statistics
    total_patients = Patient.query.count()
    active_patients = Patient.query.filter_by(status='Active').count()
    total_doctors = User.query.filter_by(role='doctor', is_active=True).count()
    total_receptionists = User.query.filter_by(role='receptionist', is_active=True).count()
    
    # Today's statistics
    today = datetime.now().date()
    new_patients_today = Patient.query.filter(
        Patient.registration_date >= today,
        Patient.registration_date < today + timedelta(days=1)
    ).count()
    
    treatments_today = Treatment.query.filter(
        Treatment.visit_date >= today,
        Treatment.visit_date < today + timedelta(days=1)
    ).count()
    
    # Recent patients
    recent_patients = Patient.query.order_by(Patient.registration_date.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         total_patients=total_patients,
                         active_patients=active_patients,
                         total_doctors=total_doctors,
                         total_receptionists=total_receptionists,
                         new_patients_today=new_patients_today,
                         treatments_today=treatments_today,
                         recent_patients=recent_patients)

@app.route('/doctor/dashboard')
@login_required
@role_required('doctor')
def doctor_dashboard():
    """Doctor dashboard with assigned patients"""
    # Get doctor's assigned patients
    assigned_patients = Patient.query.filter_by(
        assigned_doctor_id=current_user.id,
        status='Active'
    ).all()
    
    # Today's appointments/treatments
    today = datetime.now().date()
    today_treatments = Treatment.query.filter(
        Treatment.doctor_id == current_user.id,
        Treatment.visit_date >= today,
        Treatment.visit_date < today + timedelta(days=1)
    ).all()
    
    # Recent treatments
    recent_treatments = Treatment.query.filter_by(
        doctor_id=current_user.id
    ).order_by(Treatment.visit_date.desc()).limit(5).all()
    
    return render_template('doctor_dashboard.html',
                         assigned_patients=assigned_patients,
                         today_treatments=today_treatments,
                         recent_treatments=recent_treatments)

@app.route('/receptionist/dashboard')
@login_required
@role_required('receptionist')
def receptionist_dashboard():
    """Receptionist dashboard with patient management"""
    # Get recent patients
    recent_patients = Patient.query.order_by(Patient.registration_date.desc()).limit(10).all()
    
    # Get available doctors
    available_doctors = User.query.filter_by(role='doctor', is_active=True).all()
    
    # Today's registrations
    today = datetime.now().date()
    today_registrations = Patient.query.filter(
        Patient.registration_date >= today,
        Patient.registration_date < today + timedelta(days=1)
    ).count()
    
    return render_template('receptionist_dashboard.html',
                         recent_patients=recent_patients,
                         available_doctors=available_doctors,
                         today_registrations=today_registrations)

# Patient management routes
@app.route('/patients')
@login_required
def patients():
    """List all patients with search and filter"""
    search = request.args.get('search', '')
    doctor_filter = request.args.get('doctor', '')
    status_filter = request.args.get('status', '')
    
    query = Patient.query
    
    if search:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%')) |
            (Patient.patient_id.ilike(f'%{search}%')) |
            (Patient.phone.ilike(f'%{search}%'))
        )
    
    if doctor_filter:
        query = query.filter(Patient.assigned_doctor_id == doctor_filter)
    
    if status_filter:
        query = query.filter(Patient.status == status_filter)
    
    # Role-based filtering
    if current_user.role == 'doctor':
        query = query.filter(Patient.assigned_doctor_id == current_user.id)
    
    patients = query.order_by(Patient.registration_date.desc()).all()
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    
    return render_template('patients.html', 
                         patients=patients, 
                         doctors=doctors,
                         search=search,
                         doctor_filter=doctor_filter,
                         status_filter=status_filter)

@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
@role_required('receptionist')
def add_patient():
    """Add new patient"""
    if request.method == 'POST':
        try:
            patient = Patient(
                patient_id=generate_patient_id(),
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                age=int(request.form['age']),
                gender=request.form['gender'],
                phone=request.form['phone'],
                address=request.form.get('address', ''),
                email=request.form.get('email', ''),
                emergency_contact=request.form.get('emergency_contact', ''),
                emergency_phone=request.form.get('emergency_phone', ''),
                blood_type=request.form.get('blood_type', ''),
                allergies=request.form.get('allergies', ''),
                medical_history=request.form.get('medical_history', ''),
                assigned_doctor_id=int(request.form['assigned_doctor']) if request.form.get('assigned_doctor') else None,
                registered_by=current_user.id
            )
            
            db.session.add(patient)
            db.session.commit()
            
            flash(f'Patient {patient.get_full_name()} added successfully with ID: {patient.patient_id}', 'success')
            return redirect(url_for('patients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding patient: {str(e)}', 'error')
    
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    return render_template('add_patient.html', doctors=doctors)

@app.route('/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    """Edit patient information"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check permissions
    if current_user.role == 'doctor' and patient.assigned_doctor_id != current_user.id:
        flash('You can only edit patients assigned to you.', 'error')
        return redirect(url_for('patients'))
    
    if request.method == 'POST':
        try:
            # Update patient information
            patient.first_name = request.form['first_name']
            patient.last_name = request.form['last_name']
            patient.age = int(request.form['age'])
            patient.gender = request.form['gender']
            patient.phone = request.form['phone']
            patient.email = request.form.get('email', '')
            patient.address = request.form.get('address', '')
            patient.blood_type = request.form.get('blood_type', '')
            patient.allergies = request.form.get('allergies', '')
            patient.medical_history = request.form.get('medical_history', '')
            patient.emergency_contact = request.form.get('emergency_contact', '')
            patient.emergency_phone = request.form.get('emergency_phone', '')
            
            # Only admin and receptionist can change doctor assignment
            if current_user.role in ['admin', 'receptionist']:
                assigned_doctor_id = request.form.get('assigned_doctor')
                patient.assigned_doctor_id = int(assigned_doctor_id) if assigned_doctor_id else None
                patient.status = request.form.get('status', 'Active')
            
            db.session.commit()
            flash('Patient information updated successfully.', 'success')
            return redirect(url_for('patient_detail', patient_id=patient_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {str(e)}', 'error')
    
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    return render_template('edit_patient.html', patient=patient, doctors=doctors)

@app.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """Show patient details and treatment history"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check permissions
    if current_user.role == 'doctor' and patient.assigned_doctor_id != current_user.id:
        flash('You can only view patients assigned to you.', 'error')
        return redirect(url_for('patients'))
    
    # Get treatment history
    treatments = Treatment.query.filter_by(patient_id=patient_id).order_by(Treatment.visit_date.desc()).all()
    
    # Get today's date for forms
    today = datetime.now().date().strftime('%Y-%m-%d')
    return render_template('patient_detail.html', patient=patient, treatments=treatments, today=today)

# Treatment management routes
@app.route('/treatments/add/<int:patient_id>', methods=['GET', 'POST'])
@login_required
@role_required('doctor')
def add_treatment(patient_id):
    """Add new treatment for a patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if doctor is assigned to this patient
    if patient.assigned_doctor_id != current_user.id:
        flash('You can only add treatments for patients assigned to you.', 'error')
        return redirect(url_for('patients'))
    
    if request.method == 'POST':
        try:
            treatment = Treatment(
                patient_id=patient_id,
                doctor_id=current_user.id,
                visit_date=datetime.strptime(request.form['visit_date'], '%Y-%m-%dT%H:%M'),
                symptoms=request.form['symptoms'],
                diagnosis=request.form['diagnosis'],
                prescription=request.form.get('prescription', ''),
                treatment_notes=request.form.get('notes', ''),
                temperature=float(request.form['temperature']) if request.form.get('temperature') else None,
                blood_pressure=request.form.get('blood_pressure', ''),
                heart_rate=int(request.form['heart_rate']) if request.form.get('heart_rate') else None,
                weight=float(request.form['weight']) if request.form.get('weight') else None,
                follow_up_date=datetime.strptime(request.form['follow_up_date'], '%Y-%m-%d') if request.form.get('follow_up_date') else None,
                status=request.form.get('status', 'Completed')
            )
            
            db.session.add(treatment)
            db.session.commit()
            
            flash('Treatment record added successfully.', 'success')
            return redirect(url_for('patient_detail', patient_id=patient_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding treatment: {str(e)}', 'error')
    
    # Get current time for the form
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
    return render_template('add_treatment.html', patient=patient, current_time=current_time)

# User management routes (Admin only)
@app.route('/admin/users')
@login_required
@role_required('admin')
def manage_users():
    """Manage system users"""
    users = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    """Add new user"""
    if request.method == 'POST':
        try:
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                role=request.form['role'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                phone=request.form.get('phone', '')
            )
            user.set_password(request.form['password'])
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'User {user.username} added successfully.', 'success')
            return redirect(url_for('manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {str(e)}', 'error')
    
    return render_template('add_user.html')

@app.route('/patients/<int:patient_id>/discharge', methods=['POST'])
@login_required
@role_required('doctor')
def discharge_patient(patient_id):
    """Discharge a patient (doctors only)"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Check if doctor is assigned to this patient
    if patient.assigned_doctor_id != current_user.id:
        flash('You can only discharge patients assigned to you.', 'error')
        return redirect(url_for('patients'))
    
    try:
        # Update patient status
        patient.status = 'Discharged'
        
        # Create a discharge treatment record
        discharge_treatment = Treatment(
            patient_id=patient_id,
            doctor_id=current_user.id,
            visit_date=datetime.strptime(request.form['discharge_date'], '%Y-%m-%d'),
            symptoms='Discharge',
            diagnosis='Patient Discharged',
            prescription='Discharge instructions provided',
            treatment_notes=request.form.get('discharge_notes', ''),
            status='Completed'
        )
        
        db.session.add(discharge_treatment)
        db.session.commit()
        
        flash(f'Patient {patient.get_full_name()} has been discharged successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error discharging patient: {str(e)}', 'error')
    
    return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/patients/<int:patient_id>/status', methods=['POST'])
@login_required
def change_patient_status(patient_id):
    """Change patient status (admin and receptionist)"""
    if current_user.role not in ['admin', 'receptionist']:
        flash('You do not have permission to change patient status.', 'error')
        return redirect(url_for('patients'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        old_status = patient.status
        new_status = request.form['new_status']
        status_notes = request.form.get('status_notes', '')
        
        patient.status = new_status
        
        # Create a status change treatment record if notes provided
        if status_notes:
            status_treatment = Treatment(
                patient_id=patient_id,
                doctor_id=patient.assigned_doctor_id if patient.assigned_doctor_id else current_user.id,
                visit_date=datetime.now(),
                symptoms=f'Status change from {old_status} to {new_status}',
                diagnosis=f'Administrative status change',
                prescription='No prescription required',
                treatment_notes=status_notes,
                status='Completed'
            )
            db.session.add(status_treatment)
        
        db.session.commit()
        
        flash(f'Patient status changed from {old_status} to {new_status}.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing patient status: {str(e)}', 'error')
    
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Firebase Configuration Routes
@app.route('/admin/firebase-config')
@login_required
@role_required('admin')
def firebase_config_page():
    """Firebase configuration page for admin"""
    firebase_status = 'not_configured'
    firebase_project_id = None
    current_config = {}
    
    # Check if Firebase credentials file exists
    if os.path.exists('firebase_credentials.json'):
        try:
            with open('firebase_credentials.json', 'r') as f:
                current_config = json.load(f)
                firebase_status = 'configured'
                firebase_project_id = current_config.get('project_id')
        except Exception:
            pass
    
    # Count current data for migration info
    patient_count = Patient.query.count()
    treatment_count = Treatment.query.count()
    
    return render_template('firebase_config.html',
                         firebase_status=firebase_status,
                         firebase_project_id=firebase_project_id,
                         current_config=current_config,
                         patient_count=patient_count,
                         treatment_count=treatment_count)

@app.route('/admin/firebase-config', methods=['POST'])
@login_required
@role_required('admin')
def configure_firebase():
    """Configure Firebase credentials"""
    try:
        project_id = request.form.get('project_id')
        service_account_json = request.form.get('service_account_json')
        service_account_file = request.files.get('service_account_file')
        
        if not project_id:
            flash('Project ID is required.', 'error')
            return redirect(url_for('firebase_config_page'))
        
        # Get service account data
        service_account_data = None
        if service_account_file and service_account_file.filename:
            # From uploaded file
            service_account_data = json.loads(service_account_file.read().decode('utf-8'))
        elif service_account_json:
            # From pasted JSON
            service_account_data = json.loads(service_account_json)
        else:
            flash('Service account credentials are required.', 'error')
            return redirect(url_for('firebase_config_page'))
        
        # Validate service account data
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        if not all(field in service_account_data for field in required_fields):
            flash('Invalid service account JSON. Please check the file format.', 'error')
            return redirect(url_for('firebase_config_page'))
        
        # Create configuration
        firebase_config_data = {
            'project_id': project_id,
            'service_account': service_account_data,
            'configured_at': datetime.now().isoformat(),
            'configured_by': current_user.username
        }
        
        # Save configuration
        with open('firebase_credentials.json', 'w') as f:
            json.dump(firebase_config_data, f, indent=2)
        
        flash('Firebase configuration saved successfully! Restart the application to activate Firebase.', 'success')
        
    except json.JSONDecodeError:
        flash('Invalid JSON format. Please check your service account data.', 'error')
    except Exception as e:
        flash(f'Error configuring Firebase: {str(e)}', 'error')
    
    return redirect(url_for('firebase_config_page'))

@app.route('/admin/reset-firebase-config', methods=['POST'])
@login_required
@role_required('admin')
def reset_firebase_config():
    """Reset Firebase configuration"""
    try:
        if os.path.exists('firebase_credentials.json'):
            os.remove('firebase_credentials.json')
        flash('Firebase configuration reset successfully.', 'success')
    except Exception as e:
        flash(f'Error resetting Firebase configuration: {str(e)}', 'error')
    
    return redirect(url_for('firebase_config_page'))

# Initialize database
with app.app_context():
    db.create_all()
    
    # Create default admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@hospital.com',
            role='admin',
            first_name='System',
            last_name='Administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully:")
        print("Admin: admin / admin123")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)