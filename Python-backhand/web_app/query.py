#
SQL_MAKE_ADMIN_TABLE = """CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
#
SQL_MAKE_USER_TABLE = """CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""
#
SQL_MAKE_PRODUCT_TABLE = """CREATE TABLE Product(
    product_id INT NOT NULL PRIMARY KEY auto_increment,
    product_name VARCHAR(60) NOT NULL
    );
"""
#
SQL_MAKE_PO_TABLE = """CREATE TABLE po(
    po_id INT NOT NULL PRIMARY KEY auto_increment,
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    po_number VARCHAR(50) NOT NULL,
    target INT NOT NULL,
    produced INT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ); 
"""
#
SQL_MAKE_DEFECT_TABLE = """CREATE TABLE defect(
    defect_id INT NOT NULL PRIMARY KEY auto_increment,
    name VARCHRT(50) NOT NULL
    );"""
#
SQL_MAKE_CHECKER_FIELDS_TABLE = """CREATE TABLE checker_fields(
    checker_field_id INT NOT NULL PRIMARY KEY auto_increment,
    field_name VARCHAR(20) NOT NULL 
    );"""
#
SQL_MAKE_CHECKER_TABLE = """CREATE TABLE checker_output(
    id INT AUTO_INCREMENT PRIMARY KEY,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    line INT NOT NULL,
    FOREIGN KEY (product_name) REFERENCES Product(product_name),
    FOREIGN KEY (defect_id) REFERENCES defect(defect_id),
    FOREIGN KEY (field_name) REFERENCES checker_fields(field_name),
    actual_event_time TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
#
SQL_INSERT_ADMIN = 'INSERT INTO admin (username, password) VALUES (%s, %s)'
#
SQL_GET_ADMIN_INFO = 'SELECT * FROM admin WHERE username = %s'
#
SQL_GET_ADMIN_DATA_BY_ID = 'SELECT * FROM user WHERE id = %s'