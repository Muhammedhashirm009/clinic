# Patient Tracking and Treatment Management System

## Project Overview
A comprehensive web-based Patient Tracking and Treatment Management System built with Flask and PostgreSQL. The system supports role-based authentication and provides specialized dashboards for administrators, doctors, and receptionists.

## Architecture
- **Backend**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite (with Firebase migration capability)
- **Frontend**: HTML/CSS with Bootstrap 5 and Font Awesome icons
- **Authentication**: Flask-Login with role-based access control
- **Cloud Integration**: Firebase Firestore (configurable by admin)
- **Deployment**: Gunicorn WSGI server

## User Roles and Permissions

### 1. Administrator
- **Username**: admin / **Password**: admin123
- **Capabilities**:
  - View system-wide statistics and reports
  - Manage all users (doctors and receptionists)
  - Add/edit/delete doctors and receptionists
  - View all patients and their data
  - Access comprehensive analytics dashboard
  - **Configure Firebase credentials** (NEW)
  - **Migrate database to Firebase** (NEW)
  - **Note**: Only admin can create new user accounts

### 2. Doctor
- **Access**: Contact admin for account creation
- **Capabilities**:
  - View only assigned patients
  - Add/edit treatment records for assigned patients
  - View complete treatment history
  - Access patient medical records
  - Update patient information (limited)
  - Discharge patients assigned to them

### 3. Receptionist
- **Access**: Contact admin for account creation
- **Capabilities**:
  - Register new patients
  - Assign patients to available doctors
  - View all patients and their assigned doctors
  - Edit patient contact and basic information
  - Manage patient status (Active/Discharged/Inactive)

## Database Schema

### Users Table
- Role-based authentication system
- Stores admin, doctor, and receptionist accounts
- Relationships with patients and treatments

### Patients Table
- Unique auto-generated Patient ID (format: PT2025XXXX)
- Complete patient information including demographics
- Medical history and emergency contacts
- Assignment to doctors and registration tracking

### Treatments Table
- Treatment records linked to patients and doctors
- Complete visit details with symptoms, diagnosis, prescription
- Vitals tracking (temperature, BP, heart rate, weight)
- Follow-up scheduling and treatment status

### System Stats Table
- Daily statistics tracking
- Patient registration and treatment metrics
- System usage analytics

## Key Features

### Authentication & Security
- Role-based access control with Flask-Login
- Secure password hashing with Werkzeug
- Session management and user permissions
- Protected routes based on user roles

### Patient Management
- Comprehensive patient registration form
- Advanced search and filtering capabilities
- Patient assignment to doctors
- Status tracking (Active/Discharged/Inactive)
- Medical history and allergy tracking

### Treatment Management
- Complete treatment record keeping
- Vitals tracking and prescription management
- Treatment history and follow-up scheduling
- Doctor-patient assignment system

### Dashboard Analytics
- Role-specific dashboards with relevant metrics
- Real-time statistics and reporting
- Recent activity tracking
- Quick action buttons for common tasks

## User Management
The system starts with only an admin account:
- Admin account is automatically created on first run
- All doctor and receptionist accounts must be created by admin
- No demo or sample data is included for security
- Clean slate system ready for production use

## Recent Changes
- **2025-07-29**: Added Firebase configuration interface for admin users
- **2025-07-29**: Implemented database migration capability from SQLite to Firebase
- **2025-07-29**: Fixed application crashes by implementing SQLite fallback
- **2025-07-29**: Created Firebase models and configuration system
- **2025-07-18**: Complete system implementation with all core features
- **2025-07-18**: Implemented role-based dashboards with specialized functionality
- **2025-07-18**: Created comprehensive patient and treatment management system
- **2025-07-18**: Added patient discharge and status management functionality
- **2025-07-18**: Fixed treatment field name issues and registrar display
- **2025-07-18**: Removed demo credentials for security - admin-only user creation

## Technical Details
- **Flask Application**: Configured with proper database connections
- **Database Relationships**: Properly structured with foreign key constraints
- **Frontend Design**: Bootstrap 5 with responsive design
- **Form Validation**: Client-side and server-side validation
- **Error Handling**: Comprehensive error messages and user feedback

## Future Enhancements
- PDF export functionality for patient records
- Advanced reporting and analytics
- Appointment scheduling system
- Email notifications and alerts
- Mobile app compatibility
- Integration with external medical systems

## User Preferences
- Clean, professional medical interface design
- Intuitive navigation for non-technical users
- Comprehensive feature set with role-based access
- Responsive design for various screen sizes
- Clear visual hierarchy and medical color schemes