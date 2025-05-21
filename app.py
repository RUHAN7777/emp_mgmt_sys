from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
import mysql.connector
import config
import functools
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from flask_mysqldb import MySQL
app = Flask(__name__)

app.secret_key = 'v9Z$h2qM7#pT@xL!sE4&kW8rJ0fUyBvN'

# MySQL Config
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

mysql = MySQL(app)

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
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template('home.html') 


@app.route('/employee', methods=['GET', 'POST'])
@login_required
def get_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']

        cursor = mysql.connection.cursor()
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
        cursor.close()

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

    cursor = mysql.connection.cursor()
    sql = """
        INSERT INTO Employee (name, email, phone, dob, join_date, department_id, designation_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    values = (name, email, phone, dob, join_date, dept_id, desig_id)
    cursor.execute(sql, values)
    mysql.connection.commit()
    cursor.close()

    return redirect('/')

@app.route('/update', methods=['GET', 'POST'])
@login_required
def update_employee():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT emp_id, name, email, phone, dob, join_date, department_id, designation_id
            FROM Employee WHERE emp_id = %s
        """, (emp_id,))
        emp_data = cursor.fetchone()
        cursor.execute("SELECT dept_id, dept_name FROM Department")
        departments = cursor.fetchall()
        cursor.execute("SELECT designation_id, designation_name FROM Designation")
        designations = cursor.fetchall()
        cursor.close()

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

    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE Employee
        SET name = %s, email = %s, phone = %s, dob = %s, join_date = %s,
            department_id = %s, designation_id = %s
        WHERE emp_id = %s
    """, (name, email, phone, dob, join_date, department_id, designation_id, emp_id))
    mysql.connection.commit()
    cursor.close()

    return render_template('success.html', message="Employee updated successfully!")



# Step 1: Render search form
@app.route('/delete', methods=['GET'])
@login_required
def delete_search():
    return render_template('delete_search.html')

# Step 2: Process search and show delete confirmation
@app.route('/delete', methods=['POST'])
@login_required
def delete_confirm():
    emp_id = request.form['emp_id']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Employee WHERE emp_id = %s", (emp_id,))
    employee = cursor.fetchone()
    cursor.close()
    if employee:
        return render_template('delete_confirm.html', employee=employee)
    else:
        return render_template('error.html', message="Employee not found")

# Step 3: Perform deletion
@app.route('/delete/confirm', methods=['POST'])
@login_required
def delete_employee():
    emp_id = request.form['emp_id']
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM Employee WHERE emp_id = %s", (emp_id,))
        mysql.connection.commit()
        return render_template('success.html', message="Employee deleted successfully!")
    except Exception as e:
        mysql.connection.rollback()
        return render_template('error.html', message=f"Error deleting employee: {str(e)}")
    finally:
        cursor.close()


# Add WorkLog Entry Form
@app.route('/worklog', methods=['GET', 'POST'])
@login_required
def add_worklog():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        work_date = request.form['work_date']
        hours = request.form['hours_worked']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO WorkLog (emp_id, work_date, hours_worked)
            VALUES (%s, %s, %s)
        """, (emp_id, work_date, hours))
        mysql.connection.commit()
        cursor.close()

        return render_template('success.html', message="Work log added successfully!")
    
    return render_template('add_worklog.html')


# View WorkLogs by Employee ID
@app.route('/view_worklog', methods=['GET', 'POST'])
@login_required
def view_worklog():
    if request.method == 'POST':
        emp_id = request.form['emp_id']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT work_date, hours_worked
            FROM WorkLog
            WHERE emp_id = %s
            ORDER BY work_date DESC
        """, (emp_id,))
        logs = cursor.fetchall()
        cursor.close()

        return render_template('view_worklog.html', logs=logs, emp_id=emp_id)

    return render_template('view_worklog_search.html')


# Add Performance Record
@app.route('/performance', methods=['GET', 'POST'])
@login_required
def add_performance():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        review_date = request.form['review_date']
        ticket_count = request.form['ticket_count']
        review_notes = request.form['review_notes']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO Performance (emp_id, ticket_count, review_notes, review_date)
            VALUES (%s, %s, %s, %s)
        """, (emp_id, ticket_count, review_notes, review_date))
        mysql.connection.commit()
        cursor.close()

        return render_template('success.html', message="Performance record added successfully!")
    
    return render_template('add_performance.html')


# View Performance Records
@app.route('/view_performance', methods=['GET', 'POST'])
@login_required
def view_performance():
    if request.method == 'POST':
        emp_id = request.form['emp_id']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT review_date, ticket_count, review_notes
            FROM Performance
            WHERE emp_id = %s
            ORDER BY review_date DESC
        """, (emp_id,))
        records = cursor.fetchall()
        cursor.close()

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

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO Salary (emp_id, basic, hra, allowances)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            basic = VALUES(basic),
            hra = VALUES(hra),
            allowances = VALUES(allowances)
        """, (emp_id, basic, hra, allowances))
        mysql.connection.commit()
        cursor.close()

        return render_template('success.html', message='Salary added/updated successfully!')

    return render_template('add_salary.html')

@app.route('/view_salary', methods=['GET', 'POST'])
@login_required
def view_salary():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Salary WHERE emp_id = %s", (emp_id,))
        salary = cursor.fetchone()
        cursor.close()

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

        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            INSERT INTO LeaveRecord (emp_id, leave_type, leave_date, reason)
            VALUES (%s, %s, %s, %s)
        """, (emp_id, leave_type, leave_date, reason))
        mysql.connection.commit()
        cursor.close()

        return render_template('success.html', message='Leave record added successfully!')
    return render_template('add_leave.html')


@app.route('/view_leave', methods=['GET', 'POST'])
@login_required
def view_leave():
    if request.method == 'POST':
        emp_id = request.form['emp_id']

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT leave_type, leave_date, reason FROM LeaveRecord
            WHERE emp_id = %s ORDER BY leave_date DESC
        """, (emp_id,))
        leaves = cursor.fetchall()
        cursor.close()

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

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM hr WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        # user[1] = username, user[2] = password (from your table structure)
        if user and check_password_hash(user[2], password):
            session['loggedin'] = True
            session['username'] = user[1]  # Store actual username from DB
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out', 'info')  # Added feedback
    return redirect(url_for('login'))

@app.route('/register_hr', methods=['GET', 'POST'])
def register_hr():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Both fields are required', 'danger')
            return redirect(url_for('register_hr'))

        try:
            cur = mysql.connection.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS hr (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL  # Modified length
                )
            """)
            
            # Check existing user
            cur.execute("SELECT 1 FROM hr WHERE username = %s", (username,))
            if cur.fetchone():
                flash('Username already exists', 'danger')
                return redirect(url_for('register_hr'))
            
            hashed_pw = generate_password_hash(password)
            cur.execute("INSERT INTO hr (username, password) VALUES (%s, %s)", 
                       (username, hashed_pw))
            
            mysql.connection.commit()
            cur.close()
            flash('HR account created!', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('register_hr.html')


if __name__ == '__main__':
    app.run(debug=True)