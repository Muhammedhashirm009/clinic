from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'doctor', 'receptionist'
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_patients = db.relationship('Patient', foreign_keys='Patient.assigned_doctor_id', backref='assigned_doctor', lazy=True)
    treatments = db.relationship('Treatment', foreign_keys='Treatment.doctor_id', backref='doctor', lazy=True)
    registered_patients = db.relationship('Patient', foreign_keys='Patient.registered_by', backref='registered_by_user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)  # Auto-generated unique ID
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'Male', 'Female', 'Other'
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    email = db.Column(db.String(120))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    
    # Medical information
    blood_type = db.Column(db.String(5))
    allergies = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    
    # System fields
    status = db.Column(db.String(20), default='Active')  # 'Active', 'Discharged', 'Inactive'
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    registered_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    treatments = db.relationship('Treatment', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_latest_treatment(self):
        return Treatment.query.filter_by(patient_id=self.id).order_by(Treatment.created_at.desc()).first()
    
    def get_assigned_doctor(self):
        if self.assigned_doctor_id:
            return User.query.get(self.assigned_doctor_id)
        return None
    
    def get_registrar(self):
        if self.registered_by:
            return User.query.get(self.registered_by)
        return None
    
    def __repr__(self):
        return f'<Patient {self.patient_id}>'

class Treatment(db.Model):
    __tablename__ = 'treatments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Treatment details
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    symptoms = db.Column(db.Text, nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text)
    treatment_notes = db.Column(db.Text)
    follow_up_date = db.Column(db.DateTime)
    
    # Vitals
    temperature = db.Column(db.Float)
    blood_pressure = db.Column(db.String(20))
    heart_rate = db.Column(db.Integer)
    weight = db.Column(db.Float)
    
    # Status
    status = db.Column(db.String(20), default='Completed')  # 'Completed', 'Pending', 'Follow-up'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Treatment {self.id} for Patient {self.patient_id}>'

class SystemStats(db.Model):
    __tablename__ = 'system_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    stat_date = db.Column(db.Date, default=datetime.utcnow().date())
    total_patients = db.Column(db.Integer, default=0)
    active_patients = db.Column(db.Integer, default=0)
    total_treatments = db.Column(db.Integer, default=0)
    new_patients_today = db.Column(db.Integer, default=0)
    treatments_today = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemStats {self.stat_date}>'