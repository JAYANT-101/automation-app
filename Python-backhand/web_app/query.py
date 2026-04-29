#
SQL_MAKE_ADMIN_TABLE = """CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );"""
#
SQL_MAKE_USER_TABLE = """CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
"""
#
SQL_MAKE_PRODUCT_TABLE = """CREATE TABLE Product(
    id INT NOT NULL PRIMARY KEY auto_increment,
    product_name VARCHAR(60) NOT NULL
    );
"""
#
SQL_MAKE_PO_TABLE = """CREATE TABLE po(
    id INT NOT NULL PRIMARY KEY auto_increment,
    product_id INT NOT NULL ,
    po_number VARCHAR(50) NOT NULL,
    target INT NOT NULL,
    produced INT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_name
    FOREIGN KEY (product_id) 
    REFERENCES Product(id)
    ); 
"""
#
SQL_MAKE_DEFECT_TABLE = """CREATE TABLE defects(
    id INT NOT NULL PRIMARY KEY auto_increment,
    name VARCHAR(50) NOT NULL
    );"""
#
SQL_MAKE_CHECKER_FIELDS_TABLE = """CREATE TABLE checker_fields(
    id INT NOT NULL PRIMARY KEY auto_increment,
    field_name VARCHAR(20) NOT NULL 
    );"""
#
SQL_MAKE_CHECKER_TABLE = """CREATE TABLE checker_output(
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL ,
    line INT NOT NULL,
    product_id INT NOT NULL ,
    defect_id INT NOT NULL ,
    field_id INT NOT NULL ,
    actual_event_time TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_name2
    FOREIGN KEY (product_id) 
    REFERENCES Product(id),
    CONSTRAINT fk_defect_id
    FOREIGN KEY (defect_id) 
    REFERENCES defects(id),
    CONSTRAINT fk_field_name
    FOREIGN KEY (field_id) 
    REFERENCES checker_fields(id),
    CONSTRAINT fk_user_name
    FOREIGN KEY (user_id) 
    REFERENCES users(id)
);
"""
#
SQL_INSERT_ADMIN = 'INSERT INTO admin (username, password) VALUES (%s, %s)'
#
SQL_GET_ADMIN_INFO = 'SELECT * FROM admin WHERE username = %s'
#
SQL_GET_ADMIN_DATA_BY_ID = 'SELECT * FROM user WHERE id = %s'
#
SQL_INSERT_USER = 'INSERT INTO users (username, password) VALUES (%s, %s)'