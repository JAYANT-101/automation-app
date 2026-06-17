from web_app.query import *
from dotenv import load_dotenv
import  os
import DBcm
from typing import Optional
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

def setup_checker_output_db()-> None:
    """This function will creat the checker tables in the database"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_CHECKER_TABLE)

def init_db()-> None:
    """This function creates all tables"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_MAKE_ADMIN_TABLE)
        db.execute(SQL_MAKE_USER_TABLE)
        db.execute(SQL_MAKE_PRODUCT_TABLE)
        db.execute(SQL_MAKE_PO_TABLE)
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

def get_user_info(username: str)-> list[tuple]:
    """Get checker app user data by username."""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_GET_USER_INFO_BY_USERNAME, (username,))
        return db.fetchall()

def get_all_users_data():
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_SELECT_ALL_USERS_INFO)
        return db.fetchall()

def delete_user_by_username(username: str)-> None:
    """This function deletes user ny username"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_DELETE_USER_BY_USERNAME, (username,))

def is_product_in_table(product_name: str)-> int:
    """This function cheks if given product exists or not"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_IS_PRODUCT_IN_TABLE, (product_name,))
        return db.fetchall()

def is_po_in_table(po: str)-> int:
    """This function checks if the given po exists"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_IS_PO_IN_TABLE, (po,))
        return db.fetchall()
def insert_product(product_name: str)-> None:
    """This function inserts product in to the product table"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_INSERT_PRODUCT, (product_name,))

def insert_po(product_name: str, po_number: str, target: int, produced=0)-> None:
    """This function inserts data into the po table"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_INSERT_PO, (product_name, po_number, target, produced))

def insert_checker_output(
        user_id: int,
        line: int,
        po_id: int,
        field_name: str,
        defect_name: str,
        actual_event_time: str,
)-> None:
    """This function inserts data into the checker_output table"""
    with DBcm.UseDatabase(db_details) as db:
        db.execute(
            SQL_INSERT_CHECKER_OUTPUT,
            (user_id, line, po_id, field_name, defect_name, actual_event_time),
        )

def show_po_data()-> list[tuple]:
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_SHOW_PO_TABLE)
        return db.fetchall()

def get_all_product_names()-> list[str]:
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_GET_ALL_PRODUCT_NAMES)
        return [row[0] for row in db.fetchall()]

def get_po_numbers_by_product(product_name: str)-> list[tuple]:
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_GET_PO_NUMBERS_BY_PRODUCT, (product_name,))
        return db.fetchall()

def delete_po_by_number(product_name: str, po_number: str)-> None:
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_DELETE_PO_BY_NUMBER, (product_name, po_number,))

def update_po_target(product_name: str, po_number: str, target: int)-> None:
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_UPDATE_PO_TARGET, (target, product_name, po_number,))

def increment_po_produced(po_id: int)-> None:
    with DBcm.UseDatabase(db_details) as db:
        db.execute(SQL_INCREMENT_PO_PRODUCED, (po_id,))

def show_checker_output_dashboard(selected_date: Optional[str] = None)-> list[tuple]:
    with DBcm.UseDatabase(db_details) as db:
        if selected_date:
            db.execute(SQL_SHOW_CHECKER_OUTPUT_DASHBOARD_BY_DATE, (selected_date,))
        else:
            db.execute(SQL_SHOW_CHECKER_OUTPUT_DASHBOARD)
        return db.fetchall()

def get_po_defect_counts(
        po_number: str,
        selected_date: Optional[str] = None,
        line: Optional[int] = None,
)-> list[tuple]:
    with DBcm.UseDatabase(db_details) as db:
        if selected_date:
            if line is not None:
                db.execute(
                    SQL_SHOW_PO_DEFECT_COUNTS_BY_DATE_AND_LINE,
                    (po_number, selected_date, line,),
                )
            else:
                db.execute(SQL_SHOW_PO_DEFECT_COUNTS_BY_DATE, (po_number, selected_date,))
        else:
            db.execute(SQL_SHOW_PO_DEFECT_COUNTS, (po_number,))
        return db.fetchall()

def get_all_po_defect_counts(selected_date: Optional[str] = None)-> list[tuple]:
    with DBcm.UseDatabase(db_details) as db:
        if selected_date:
            db.execute(SQL_SHOW_ALL_PO_DEFECT_COUNTS_BY_DATE, (selected_date,))
        else:
            db.execute(SQL_SHOW_ALL_PO_DEFECT_COUNTS)
        return db.fetchall()
