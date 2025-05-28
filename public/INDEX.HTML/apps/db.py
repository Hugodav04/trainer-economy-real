import mysql.connector
from mysql.connector import Error
 
def get_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3307,
            user="root",
            
            database="trainers"
        )
        return connection
    except Error as e:
        print("❌ Error al conectar a la base de datos:", e)
        return None