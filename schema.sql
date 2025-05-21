-- Department Table
CREATE TABLE Department (
    dept_id INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) UNIQUE NOT NULL
);

-- Designation Table
CREATE TABLE Designation (
    designation_id INT AUTO_INCREMENT PRIMARY KEY,
    designation_name VARCHAR(100) NOT NULL,
    level INT DEFAULT 1
);

-- Employee Table
CREATE TABLE Employee (
    emp_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    dob DATE,
    join_date DATE,
    department_id INT,
    designation_id INT,
    FOREIGN KEY (department_id) REFERENCES Department(dept_id),
    FOREIGN KEY (designation_id) REFERENCES Designation(designation_id)
);

-- WorkLog Table with CASCADE
CREATE TABLE WorkLog (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT,
    work_date DATE,
    hours_worked DECIMAL(4,2),
    FOREIGN KEY (emp_id) REFERENCES Employee(emp_id) ON DELETE CASCADE
);

-- Performance Table with CASCADE
CREATE TABLE Performance (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT,
    ticket_count INT DEFAULT 0,
    review_notes TEXT,
    review_date DATE,
    FOREIGN KEY (emp_id) REFERENCES Employee(emp_id) ON DELETE CASCADE
);

-- Salary Table with CASCADE
CREATE TABLE Salary (
    salary_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT,
    basic DECIMAL(10, 2),
    hra DECIMAL(10, 2),
    allowances DECIMAL(10, 2),
    FOREIGN KEY (emp_id) REFERENCES Employee(emp_id) ON DELETE CASCADE
);

-- LeaveRecord Table with CASCADE
CREATE TABLE LeaveRecord (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    emp_id INT,
    leave_type VARCHAR(50),
    leave_date DATE,
    reason TEXT,
    FOREIGN KEY (emp_id) REFERENCES Employee(emp_id) ON DELETE CASCADE
);

CREATE TABLE hr (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
