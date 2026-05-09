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
    product_name VARCHAR(60) UNIQUE NOT NULL
    );
"""
#
SQL_MAKE_PO_TABLE = """CREATE TABLE po(
    id INT NOT NULL PRIMARY KEY auto_increment,
    product_name VARCHAR(60) NOT NULL,
    po_number VARCHAR(50)  NOT NULL,
    target INT NOT NULL,
    produced INT NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_name
    FOREIGN KEY (product_name) 
    REFERENCES Product(product_name)
    ); 
"""
SQL_MAKE_CHECKER_TABLE = """CREATE TABLE checker_output(
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL ,
    line INT NOT NULL,
    po_id INT NOT NULL,
    defect_name VARCHAR(50) NOT NULL,
    field_name VARCHAR(20) NOT NULL  ,
    actual_event_time TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_name
    FOREIGN KEY (user_id) 
    REFERENCES users(id),
    CONSTRAINT fk_po_id
    FOREIGN KEY (po_id) 
    REFERENCES po(id)
);
"""
#
SQL_INSERT_ADMIN = 'INSERT INTO admin (username, password) VALUES (%s, %s)'
#
SQL_GET_ADMIN_INFO = 'SELECT * FROM admin WHERE username = %s'
#
SQL_GET_ADMIN_DATA_BY_ID = 'SELECT * FROM admin WHERE id = %s'
#
SQL_INSERT_USER = 'INSERT INTO users (username, password) VALUES (%s, %s)'
#
SQL_SELECT_ALL_USERS_INFO = 'SELECT id,username FROM users'
#
SQL_DELETE_USER_BY_USERNAME = 'DELETE FROM users WHERE username=%s;'
#
SQL_IS_PRODUCT_IN_TABLE = 'SELECT EXISTS(SELECT 1 FROM Product WHERE product_name = %s);'
#
SQL_IS_PO_IN_TABLE = 'SELECT EXISTS(SELECT 1 FROM po WHERE po_number = %s);'
#
SQL_INSERT_PRODUCT = 'INSERT INTO Product (product_name) VALUES (%s);'
#
SQL_INSERT_PO = 'INSERT INTO po (product_name, po_number, target, produced) VALUES (%s,%s,%s,%s);'
#
SQL_SHOW_PO_TABLE = 'SELECT product_name,po_number,target FROM po'
#
SQL_GET_ALL_PRODUCT_NAMES = 'SELECT product_name FROM Product ORDER BY product_name;'
#
SQL_GET_PO_NUMBERS_BY_PRODUCT = 'SELECT po_number,target FROM po WHERE product_name = %s ORDER BY po_number;'
#
SQL_DELETE_PO_BY_NUMBER = 'DELETE FROM po WHERE product_name = %s AND po_number = %s;'
#
SQL_UPDATE_PO_TARGET = 'UPDATE po SET target = %s WHERE product_name = %s AND po_number = %s;'
