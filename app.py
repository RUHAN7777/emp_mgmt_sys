from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import functools
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Secret Key and DB config from .env
app.secret_key = os.getenv('SECRET_KEY')

# Create PyMySQL connection
def get_db_connection():
    return pymysql.connect(
        host = os.environ['MYSQL_HOST']
        user = os.environ['MYSQL_USER']
        password = os.environ['MYSQL_PASSWORD']
        database = os.environ['MYSQL_DATABASE']
        port=int(os.environ.get('DB_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10
    )

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('loggedin'):
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def dashboard():
    return render_template('home.html')


@app.route('/employee', methods=['GET', 'POST'])
@login_required
def get_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT e.emp_id, e.name, e.email, e.phone, d.dept_name, ds.designation_name, 
                       wl.hours_worked, p.ticket_count, p.review_notes
                FROM Employee e
                LEFT JOIN Department d ON e.department_id = d.dept_id
                LEFT JOIN Designation ds ON e.designation_id = ds.designation_id
                LEFT JOIN WorkLog wl ON e.emp_id = wl.emp_id
                LEFT JOIN Performance p ON e.emp_id = p.emp_id
                WHERE e.emp_id = %s
                LIMIT 1;
            """, (emp_id,))
            data = cursor.fetchone()
        conn.close()

        if data:
            return render_template('employee_details.html', data=data)
        else:
            return render_template('error.html', message='Employee not found.')

    return render_template('index.html')

@app.route('/add')
@login_required
def add_form():
    return render_template('add_employee.html')


@app.route('/add_employee', methods=['POST'])
@login_required
def add_employee():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    dob = request.form['dob']
    join_date = request.form['join_date']
    dept_id = request.form['department_id']
    desig_id = request.form['designation_id']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = """
            INSERT INTO Employee (name, email, phone, dob, join_date, department_id, designation_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (name, email, phone, dob, join_date, dept_id, desig_id)
        cursor.execute(sql, values)
    conn.close()

    return redirect('/')


@app.route('/update', methods=['GET', 'POST'])
@login_required
def update_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT emp_id, name, email, phone, dob, join_date, department_id, designation_id
                FROM Employee WHERE emp_id = %s
            """, (emp_id,))
            emp_data = cursor.fetchone()

            cursor.execute("SELECT dept_id, dept_name FROM Department")
            departments = cursor.fetchall()
            cursor.execute("SELECT designation_id, designation_name FROM Designation")
            designations = cursor.fetchall()
        conn.close()

        if emp_data:
            return render_template('update_form.html', emp=emp_data, departments=departments, designations=designations)
        else:
            return render_template('error.html', message="Employee not found.")
    return render_template('update_search.html')


@app.route('/submit_update', methods=['POST'])
@login_required
def submit_update():
    emp_id = request.form['emp_id']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    dob = request.form['dob']
    join_date = request.form['join_date']
    department_id = request.form['department_id']
    designation_id = request.form['designation_id']

    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            UPDATE Employee
            SET name = %s, email = %s, phone = %s, dob = %s, join_date = %s,
                department_id = %s, designation_id = %s
            WHERE emp_id = %s
        """, (name, email, phone, dob, join_date, department_id, designation_id, emp_id))
    conn.close()

    return render_template('success.html', message="Employee updated successfully!")

@app.route('/delete', methods=['GET'])
@login_required
def delete_search():
    return render_template('delete_search.html')


@app.route('/delete', methods=['POST'])
@login_required
def delete_confirm():
    emp_id = request.form['emp_id']
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM Employee WHERE emp_id = %s", (emp_id,))
        employee = cursor.fetchone()
    conn.close()

    if employee:
        return render_template('delete_confirm.html', employee=employee)
    else:
        return render_template('error.html', message="Employee not found")


@app.route('/delete/confirm', methods=['POST'])
@login_required
def delete_employee():
    emp_id = request.form['emp_id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Employee WHERE emp_id = %s", (emp_id,))
        conn.commit()
        return render_template('success.html', message="Employee deleted successfully!")
    except Exception as e:
        conn.rollback()
        return render_template('error.html', message=f"Error deleting employee: {str(e)}")
    finally:
        conn.close()

@app.route('/worklog', methods=['GET', 'POST'])
@login_required
def add_worklog():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        work_date = request.form['work_date']
        hours = request.form['hours_worked']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO WorkLog (emp_id, work_date, hours_worked)
                VALUES (%s, %s, %s)
            """, (emp_id, work_date, hours))
        conn.commit()
        conn.close()

        return render_template('success.html', message="Work log added successfully!")

    return render_template('add_worklog.html')


@app.route('/view_worklog', methods=['GET', 'POST'])
@login_required
def view_worklog():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT work_date, hours_worked
                FROM WorkLog
                WHERE emp_id = %s
                ORDER BY work_date DESC
            """, (emp_id,))
            logs = cursor.fetchall()
        conn.close()
        return render_template('view_worklog.html', logs=logs, emp_id=emp_id)

    return render_template('view_worklog_search.html')

@app.route('/performance', methods=['GET', 'POST'])
@login_required
def add_performance():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        review_date = request.form['review_date']
        ticket_count = request.form['ticket_count']
        review_notes = request.form['review_notes']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Performance (emp_id, ticket_count, review_notes, review_date)
                VALUES (%s, %s, %s, %s)
            """, (emp_id, ticket_count, review_notes, review_date))
        conn.commit()
        conn.close()

        return render_template('success.html', message="Performance record added successfully!")
    return render_template('add_performance.html')


@app.route('/view_performance', methods=['GET', 'POST'])
@login_required
def view_performance():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT review_date, ticket_count, review_notes
                FROM Performance
                WHERE emp_id = %s
                ORDER BY review_date DESC
            """, (emp_id,))
            records = cursor.fetchall()
        conn.close()
        return render_template('view_performance.html', records=records, emp_id=emp_id)

    return render_template('view_performance_search.html')

@app.route('/salary', methods=['GET', 'POST'])
@login_required
def salary():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        basic = request.form['basic']
        hra = request.form['hra']
        allowances = request.form['allowances']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO Salary (emp_id, basic, hra, allowances)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                basic = VALUES(basic),
                hra = VALUES(hra),
                allowances = VALUES(allowances)
            """, (emp_id, basic, hra, allowances))
        conn.commit()
        conn.close()

        return render_template('success.html', message='Salary added/updated successfully!')

    return render_template('add_salary.html')


@app.route('/view_salary', methods=['GET', 'POST'])
@login_required
def view_salary():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Salary WHERE emp_id = %s", (emp_id,))
            salary = cursor.fetchone()
        conn.close()

        if salary:
            return render_template('view_salary.html', salary=salary)
        else:
            return render_template('error.html', message='No salary record found for this employee.')

    return render_template('view_salary_search.html')


@app.route('/add_leave', methods=['GET', 'POST'])
@login_required
def add_leave():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        leave_type = request.form['leave_type']
        leave_date = request.form['leave_date']
        reason = request.form['reason']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO LeaveRecord (emp_id, leave_type, leave_date, reason)
                VALUES (%s, %s, %s, %s)
            """, (emp_id, leave_type, leave_date, reason))
        conn.commit()
        conn.close()

        return render_template('success.html', message='Leave record added successfully!')
    return render_template('add_leave.html')


@app.route('/view_leave', methods=['GET', 'POST'])
@login_required
def view_leave():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT leave_type, leave_date, reason FROM LeaveRecord
                WHERE emp_id = %s ORDER BY leave_date DESC
            """, (emp_id,))
            leaves = cursor.fetchall()
        conn.close()

        if leaves:
            return render_template('view_leave.html', leaves=leaves, emp_id=emp_id)
        else:
            return render_template('error.html', message='No leave records found for this employee.')

    return render_template('view_leave_search.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM HR WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register_hr', methods=['GET', 'POST'])
def register_hr():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO HR (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return render_template('error.html', message=f"Error registering HR: {str(e)}")
        finally:
            conn.close()

        return render_template('success.html', message='HR registered successfully!')

    return render_template('register_hr.html')

if __name__ == '__main__':
    app.run(debug=True)
