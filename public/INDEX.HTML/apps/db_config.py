import mysql.connector

# Conectar con las bases de datos de zapatillas
def conectar_bd():
    return {
        "Nike": mysql.connector.connect(
            host="localhost", user="usuario_nike", password="contraseña_nike", database="nike_db"
        ),
        "Adidas": mysql.connector.connect(
            host="localhost", user="usuario_adidas", password="contraseña_adidas", database="adidas_db"
        ),
        "Asics": mysql.connector.connect(
            host="localhost", user="usuario_asics", password="contraseña_asics", database="asics_db"
        ),
        "Reebok": mysql.connector.connect(
            host="localhost", user="usuario_reebok", password="contraseña_reebok", database="reebok_db"
        )
    }