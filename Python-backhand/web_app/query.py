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
    field_name VARCHAR(20) NOT NULL ,
    defect_name VARCHAR(50),
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
SQL_GET_USER_INFO_BY_USERNAME = 'SELECT id, username, password FROM users WHERE username = %s'
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
SQL_INSERT_CHECKER_OUTPUT = 'INSERT INTO checker_output (user_id, line, po_id, field_name, defect_name, actual_event_time) VALUES (%s,%s,%s,%s,%s,%s);'
#
SQL_SHOW_PO_TABLE = 'SELECT product_name,po_number,target FROM po'
#
SQL_GET_ALL_PRODUCT_NAMES = 'SELECT product_name FROM Product ORDER BY product_name;'
#
SQL_GET_PO_NUMBERS_BY_PRODUCT = 'SELECT id, po_number, target FROM po WHERE product_name = %s ORDER BY po_number;'
#
SQL_DELETE_PO_BY_NUMBER = 'DELETE FROM po WHERE product_name = %s AND po_number = %s;'
#
SQL_UPDATE_PO_TARGET = 'UPDATE po SET target = %s WHERE product_name = %s AND po_number = %s;'
#
SQL_INCREMENT_PO_PRODUCED = 'UPDATE po SET produced = produced + 1 WHERE id = %s;'
#
SQL_SHOW_CHECKER_OUTPUT_DASHBOARD = """
SELECT
    po.po_number,
    po.product_name,
    po.target,
    po.produced,
    COALESCE(SUM(CASE WHEN checker_output.field_name = 'pass' THEN 1 ELSE 0 END), 0) AS pass_count,
    COALESCE(SUM(CASE WHEN checker_output.field_name = 'reject' THEN 1 ELSE 0 END), 0) AS reject_count,
    COALESCE(SUM(CASE WHEN checker_output.field_name = 'alter' THEN 1 ELSE 0 END), 0) AS alter_count
FROM po
LEFT JOIN checker_output
    ON checker_output.po_id = po.id
GROUP BY po.id, po.po_number, po.product_name, po.target, po.produced
ORDER BY po.po_number;
"""

SQL_SHOW_CHECKER_OUTPUT_DASHBOARD_BY_DATE = """
SELECT
    po.po_number,
    po.product_name,
    po.target,
    checker_output.line,
    COALESCE(SUM(CASE WHEN checker_output.field_name = 'pass' THEN 1 ELSE 0 END), 0) AS pass_count,
    COALESCE(SUM(CASE WHEN checker_output.field_name = 'reject' THEN 1 ELSE 0 END), 0) AS reject_count,
    COALESCE(SUM(CASE WHEN checker_output.field_name = 'alter' THEN 1 ELSE 0 END), 0) AS alter_count
FROM checker_output
JOIN po
    ON checker_output.po_id = po.id
WHERE DATE(checker_output.recorded_at) = %s
GROUP BY checker_output.line, po.id, po.po_number, po.product_name, po.target
ORDER BY checker_output.line, po.po_number;
"""

SQL_SHOW_PO_DEFECT_COUNTS = """
SELECT
    po.product_name,
    po.po_number,
    COALESCE(NULLIF(checker_output.defect_name, ''), 'Unknown') AS defect_name,
    COUNT(*) AS defect_count
FROM po
JOIN checker_output
    ON checker_output.po_id = po.id
WHERE po.po_number = %s
    AND checker_output.field_name = 'alter'
GROUP BY po.product_name, po.po_number, defect_name
ORDER BY defect_count DESC, defect_name;
"""

SQL_SHOW_PO_DEFECT_COUNTS_BY_DATE = """
SELECT
    po.product_name,
    po.po_number,
    checker_output.line,
    COALESCE(NULLIF(checker_output.defect_name, ''), 'Unknown') AS defect_name,
    COUNT(*) AS defect_count
FROM po
JOIN checker_output
    ON checker_output.po_id = po.id
WHERE po.po_number = %s
    AND checker_output.field_name = 'alter'
    AND DATE(checker_output.recorded_at) = %s
GROUP BY po.product_name, po.po_number, checker_output.line, defect_name
ORDER BY checker_output.line, defect_count DESC, defect_name;
"""

SQL_SHOW_PO_DEFECT_COUNTS_BY_DATE_AND_LINE = """
SELECT
    po.product_name,
    po.po_number,
    checker_output.line,
    COALESCE(NULLIF(checker_output.defect_name, ''), 'Unknown') AS defect_name,
    COUNT(*) AS defect_count
FROM po
JOIN checker_output
    ON checker_output.po_id = po.id
WHERE po.po_number = %s
    AND checker_output.field_name = 'alter'
    AND DATE(checker_output.recorded_at) = %s
    AND checker_output.line = %s
GROUP BY po.product_name, po.po_number, checker_output.line, defect_name
ORDER BY defect_count DESC, defect_name;
"""

SQL_SHOW_ALL_PO_DEFECT_COUNTS = """
SELECT
    COALESCE(NULLIF(checker_output.defect_name, ''), 'Unknown') AS defect_name,
    COUNT(*) AS defect_count
FROM checker_output
WHERE checker_output.field_name = 'alter'
GROUP BY defect_name
ORDER BY defect_count DESC, defect_name;
"""

SQL_SHOW_ALL_PO_DEFECT_COUNTS_BY_DATE = """
SELECT
    COALESCE(NULLIF(checker_output.defect_name, ''), 'Unknown') AS defect_name,
    COUNT(*) AS defect_count
FROM checker_output
WHERE checker_output.field_name = 'alter'
    AND DATE(checker_output.recorded_at) = %s
GROUP BY defect_name
ORDER BY defect_count DESC, defect_name;
"""
