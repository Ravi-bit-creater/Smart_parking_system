import mysql.connector

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="smart_parking"
        )
        return conn
    except mysql.connector.Error as e:
        print("Database error:", e)
        return None
