### Introduction

The **Medical Scheduler** is a web platform designed to optimize medical appointment scheduling. This system provides comprehensive features for patients, doctors, and clinic administrators.

---

### System Architecture

#### Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python with Flask
- **Database**: SQLite
- **Dependency Management**: pip

#### Folder Structure

- `app/`: Contains the main application files.
  - `templates/`: HTML files.
  - `static/`: CSS, JS, and image files.
  - `routes.py`: Manages application routes.
  - `models.py`: Defines database models.
  - `forms.py`: Defines forms used in the application.

---

### Main Features

#### Appointment Scheduling

- Patients can select doctors, dates, and available times.
- Doctors can view and manage their schedules.

#### User Registration

- Registration of patients and professionals with data validation.
- Update and delete users via admin panel.

#### Notifications

- Email reminders to notify patients about upcoming appointments.

---

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/joaoportolan93/medical-scheduler.git
   cd medical-scheduler
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   flask init-db
   ```

5. Start the server:
   ```bash
   flask run
   ```

Access the system at [http://localhost:5000](http://localhost:5000).

