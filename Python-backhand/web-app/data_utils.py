from query import *
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

def inti_db()-> None:
    """This function creates all tables"""
    setup_admin_db()
    setup_user_db()
    setup_product_db()
    setup_po_db()
    setup_defect_db()
    setup_checker_fields_db()
    setup_checker_db()

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

def setup_checker_db()-> None:
    """This function will creat the checker tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_CHECKER_TABLE)
