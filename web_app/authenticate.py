# MySQL boilerplate from https://www.freecodecamp.org/news/connect-python-with-sql/

import mysql.connector
from mysql.connector import Error

def login(username, password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host = "localhost",
            user="root",
            passwd="Motocod19**"
        )
    except Error as err:
        print(f"Error: {err}")
    
    cursor = connection.cursor()
    
    try:
        cursor.execute(f"""
                       SELECT isAdmin, courseGroup 
                       FROM login_details 
                       WHERE username={hash(username)} AND password={hash(password)}
                       """)
        
        results = cursor.fetchall()
        
        results = [result for result in results]
        
        if len(results) == 0:
            raise LoginFailure
        
        return bool(results[0][0]), results[0][1]
    except Error as err:
        print(f"Error: {err}")

class LoginFailure(Exception):
    pass
        