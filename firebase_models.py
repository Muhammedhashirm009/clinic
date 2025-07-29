from datetime import datetime, timedelta
from firebase_config import firebase_config
import uuid

class FirebaseUser:
    def __init__(self, data=None, doc_id=None):
        self.id = doc_id
        self.username = data.get('username', '') if data else ''
        self.email = data.get('email', '') if data else ''
        self.role = data.get('role', '') if data else ''
        self.first_name = data.get('first_name', '') if data else ''
        self.last_name = data.get('last_name', '') if data else ''
        self.phone = data.get('phone', '') if data else ''
        self.is_active = data.get('is_active', True) if data else True
        self.created_at = data.get('created_at') if data else datetime.now()
        self.updated_at = data.get('updated_at') if data else datetime.now()
        
    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @staticmethod
    def get_by_username(username):
        if not firebase_config.is_configured():
            return None
        try:
            users_ref = firebase_config.db.collection('users')
            query = users_ref.where('username', '==', username).limit(1)
            docs = query.stream()
            for doc in docs:
                return FirebaseUser(doc.to_dict(), doc.id)
        except Exception as e:
            print(f"Error getting user by username: {e}")
        return None
    
    @staticmethod
    def get_by_id(user_id):
        if not firebase_config.is_configured():
            return None
        try:
            doc_ref = firebase_config.db.collection('users').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return FirebaseUser(doc.to_dict(), doc.id)
        except Exception as e:
            print(f"Error getting user by ID: {e}")
        return None
    
    @staticmethod
    def get_all():
        if not firebase_config.is_configured():
            return []
        try:
            users_ref = firebase_config.db.collection('users')
            docs = users_ref.stream()
            return [FirebaseUser(doc.to_dict(), doc.id) for doc in docs]
        except Exception as e:
            print(f"Error getting all users: {e}")
        return []
    
    @staticmethod
    def get_by_role(role):
        if not firebase_config.is_configured():
            return []
        try:
            users_ref = firebase_config.db.collection('users')
            query = users_ref.where('role', '==', role).where('is_active', '==', True)
            docs = query.stream()
            return [FirebaseUser(doc.to_dict(), doc.id) for doc in docs]
        except Exception as e:
            print(f"Error getting users by role: {e}")
        return []
    
    def save(self):
        if not firebase_config.is_configured():
            return False
        try:
            self.updated_at = datetime.now()
            if self.id:
                # Update existing
                firebase_config.db.collection('users').document(self.id).set(self.to_dict())
            else:
                # Create new
                doc_ref = firebase_config.db.collection('users').add(self.to_dict())
                self.id = doc_ref[1].id
            return True
        except Exception as e:
            print(f"Error saving user: {e}")
            return False

class FirebasePatient:
    def __init__(self, data=None, doc_id=None):
        self.id = doc_id
        self.patient_id = data.get('patient_id', '') if data else ''
        self.first_name = data.get('first_name', '') if data else ''
        self.last_name = data.get('last_name', '') if data else ''
        self.age = data.get('age', 0) if data else 0
        self.gender = data.get('gender', '') if data else ''
        self.phone = data.get('phone', '') if data else ''
        self.address = data.get('address', '') if data else ''
        self.email = data.get('email', '') if data else ''
        self.emergency_contact = data.get('emergency_contact', '') if data else ''
        self.emergency_phone = data.get('emergency_phone', '') if data else ''
        self.blood_type = data.get('blood_type', '') if data else ''
        self.allergies = data.get('allergies', '') if data else ''
        self.medical_history = data.get('medical_history', '') if data else ''
        self.status = data.get('status', 'Active') if data else 'Active'
        self.assigned_doctor_id = data.get('assigned_doctor_id', '') if data else ''
        self.registered_by = data.get('registered_by', '') if data else ''
        self.registration_date = data.get('registration_date') if data else datetime.now()
        self.updated_at = data.get('updated_at') if data else datetime.now()
    
    def to_dict(self):
        return {
            'patient_id': self.patient_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'gender': self.gender,
            'phone': self.phone,
            'address': self.address,
            'email': self.email,
            'emergency_contact': self.emergency_contact,
            'emergency_phone': self.emergency_phone,
            'blood_type': self.blood_type,
            'allergies': self.allergies,
            'medical_history': self.medical_history,
            'status': self.status,
            'assigned_doctor_id': self.assigned_doctor_id,
            'registered_by': self.registered_by,
            'registration_date': self.registration_date,
            'updated_at': self.updated_at
        }
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_assigned_doctor(self):
        if self.assigned_doctor_id:
            return FirebaseUser.get_by_id(self.assigned_doctor_id)
        return None
    
    def get_registrar(self):
        if self.registered_by:
            return FirebaseUser.get_by_id(self.registered_by)
        return None
    
    @staticmethod
    def get_all():
        if not firebase_config.is_configured():
            return []
        try:
            patients_ref = firebase_config.db.collection('patients')
            docs = patients_ref.order_by('registration_date', direction=firestore.Query.DESCENDING).stream()
            return [FirebasePatient(doc.to_dict(), doc.id) for doc in docs]
        except Exception as e:
            print(f"Error getting all patients: {e}")
        return []
    
    @staticmethod
    def get_by_id(patient_id):
        if not firebase_config.is_configured():
            return None
        try:
            doc_ref = firebase_config.db.collection('patients').document(patient_id)
            doc = doc_ref.get()
            if doc.exists:
                return FirebasePatient(doc.to_dict(), doc.id)
        except Exception as e:
            print(f"Error getting patient by ID: {e}")
        return None
    
    @staticmethod
    def get_by_doctor(doctor_id):
        if not firebase_config.is_configured():
            return []
        try:
            patients_ref = firebase_config.db.collection('patients')
            query = patients_ref.where('assigned_doctor_id', '==', doctor_id)
            docs = query.stream()
            return [FirebasePatient(doc.to_dict(), doc.id) for doc in docs]
        except Exception as e:
            print(f"Error getting patients by doctor: {e}")
        return []
    
    @staticmethod
    def search(search_term):
        if not firebase_config.is_configured():
            return []
        try:
            patients = FirebasePatient.get_all()
            results = []
            search_lower = search_term.lower()
            for patient in patients:
                if (search_lower in patient.first_name.lower() or 
                    search_lower in patient.last_name.lower() or 
                    search_lower in patient.patient_id.lower() or 
                    search_lower in patient.phone.lower()):
                    results.append(patient)
            return results
        except Exception as e:
            print(f"Error searching patients: {e}")
        return []
    
    def save(self):
        if not firebase_config.is_configured():
            return False
        try:
            self.updated_at = datetime.now()
            if self.id:
                # Update existing
                firebase_config.db.collection('patients').document(self.id).set(self.to_dict())
            else:
                # Create new
                doc_ref = firebase_config.db.collection('patients').add(self.to_dict())
                self.id = doc_ref[1].id
            return True
        except Exception as e:
            print(f"Error saving patient: {e}")
            return False

class FirebaseTreatment:
    def __init__(self, data=None, doc_id=None):
        self.id = doc_id
        self.patient_id = data.get('patient_id', '') if data else ''
        self.doctor_id = data.get('doctor_id', '') if data else ''
        self.visit_date = data.get('visit_date') if data else datetime.now()
        self.symptoms = data.get('symptoms', '') if data else ''
        self.diagnosis = data.get('diagnosis', '') if data else ''
        self.prescription = data.get('prescription', '') if data else ''
        self.treatment_notes = data.get('treatment_notes', '') if data else ''
        self.follow_up_date = data.get('follow_up_date') if data else None
        self.temperature = data.get('temperature') if data else None
        self.blood_pressure = data.get('blood_pressure', '') if data else ''
        self.heart_rate = data.get('heart_rate') if data else None
        self.weight = data.get('weight') if data else None
        self.status = data.get('status', 'Completed') if data else 'Completed'
        self.created_at = data.get('created_at') if data else datetime.now()
        self.updated_at = data.get('updated_at') if data else datetime.now()
    
    def to_dict(self):
        return {
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'visit_date': self.visit_date,
            'symptoms': self.symptoms,
            'diagnosis': self.diagnosis,
            'prescription': self.prescription,
            'treatment_notes': self.treatment_notes,
            'follow_up_date': self.follow_up_date,
            'temperature': self.temperature,
            'blood_pressure': self.blood_pressure,
            'heart_rate': self.heart_rate,
            'weight': self.weight,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @property
    def doctor(self):
        return FirebaseUser.get_by_id(self.doctor_id)
    
    @property
    def patient(self):
        return FirebasePatient.get_by_id(self.patient_id)
    
    @staticmethod
    def get_by_patient(patient_id):
        if not firebase_config.is_configured():
            return []
        try:
            treatments_ref = firebase_config.db.collection('treatments')
            query = treatments_ref.where('patient_id', '==', patient_id).order_by('visit_date', direction=firestore.Query.DESCENDING)
            docs = query.stream()
            return [FirebaseTreatment(doc.to_dict(), doc.id) for doc in docs]
        except Exception as e:
            print(f"Error getting treatments by patient: {e}")
        return []
    
    @staticmethod
    def get_by_doctor(doctor_id):
        if not firebase_config.is_configured():
            return []
        try:
            treatments_ref = firebase_config.db.collection('treatments')
            query = treatments_ref.where('doctor_id', '==', doctor_id).order_by('visit_date', direction=firestore.Query.DESCENDING)
            docs = query.stream()
            return [FirebaseTreatment(doc.to_dict(), doc.id) for doc in docs]
        except Exception as e:
            print(f"Error getting treatments by doctor: {e}")
        return []
    
    def save(self):
        if not firebase_config.is_configured():
            return False
        try:
            self.updated_at = datetime.now()
            if self.id:
                # Update existing
                firebase_config.db.collection('treatments').document(self.id).set(self.to_dict())
            else:
                # Create new
                doc_ref = firebase_config.db.collection('treatments').add(self.to_dict())
                self.id = doc_ref[1].id
            return True
        except Exception as e:
            print(f"Error saving treatment: {e}")
            return False

def generate_patient_id():
    """Generate unique patient ID"""
    import random
    while True:
        year = datetime.now().year
        random_num = random.randint(1000, 9999)
        patient_id = f"PT{year}{random_num}"
        
        # Check if ID already exists in Firebase
        if not firebase_config.is_configured():
            return patient_id
            
        try:
            patients_ref = firebase_config.db.collection('patients')
            query = patients_ref.where('patient_id', '==', patient_id).limit(1)
            docs = list(query.stream())
            if not docs:
                return patient_id
        except Exception:
            return patient_id