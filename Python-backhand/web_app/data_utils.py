from web_app.query import *
from dotenv import load_dotenv
import  os
import DBcm
#Loding all the details to connet to the databse
load_dotenv()
db_details = {
    'host' : os.getenv('DB_HOSt'),
    'database' : os.getenv('DB_DATABASE'),
    'user' : os.getenv('DB_USER'),
    'password' : os.getenv('DB_PASSWORD')
}

def setup_user_db()-> None:
    """This function will creat the user tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_USER_TABLE)

def setup_admin_db()-> None:
    """This function will creat the admin tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_ADMIN_TABLE)

def setup_product_db()-> None:
    """This function will creat the product tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_PRODUCT_TABLE)

def setup_po_db()-> None:
    """This function will creat the po tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_PO_TABLE)

def setup_defect_db()-> None:
    """This function will creat the defect tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_DEFECT_TABLE)

def setup_checker_fields_db()-> None:
    """This function will creat the checker_fields tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_CHECKER_FIELDS_TABLE)

def setup_checker_output_db()-> None:
    """This function will creat the checker tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_CHECKER_TABLE)

def init_db()-> None:
    """This function creates all tables"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_USER_TABLE)
        db.execute(SQL_MAKE_ADMIN_TABLE)
        db.execute(SQL_MAKE_PRODUCT_TABLE)
        db.execute(SQL_MAKE_PO_TABLE)
        db.execute(SQL_MAKE_DEFECT_TABLE)
        db.execute(SQL_MAKE_CHECKER_FIELDS_TABLE)
        db.execute(SQL_MAKE_CHECKER_TABLE)

def insert_admin_in_admin_table(username:str, password)-> None:
    """This function insert user in the user table"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_INSERT_ADMIN,(username, password))

def get_admin_info(username:str)->dict:
    """This function get data of the admin based on the username"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_GET_ADMIN_INFO, (username,))
        return db.fetchall()

def get_admin_info_by_id(id)->dict:
    """This function get data of the admin based on the id"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_GET_ADMIN_DATA_BY_ID, (id,))
        return db.fetchall()

def insert_user_in_users_table(username:str, password)-> None:
    """Takes two arguments and add user in the users table """
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_INSERT_USER, (username, password,))

def get_all_users_data():
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_SELECT_ALL_USERS_INFO)
        return db.fetchall()

def delete_user_by_username(username: str)-> None:
    """This function deletes user ny username"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_DELETE_USER_BY_USERNAME, (username,))