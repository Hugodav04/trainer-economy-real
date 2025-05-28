from flask import Flask, request, jsonify, render_template
from scraper import setup_driver, scrape_eci, scrape_footlocker, scrape_courir, scrape_footdistrict
from db import get_connection
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('proyecto.html', resultados=[]) # Inicializamos con una lista vacía

@app.route('/buscar', methods=['GET'])
def buscar():
    
    marca = request.args.get('marca')
    modelo = request.args.get('modelo')

    if not marca or not modelo:
        return jsonify({"error": "Debes proporcionar la marca y el modelo."}), 400

    conn = get_connection()
    resultados_db = [] # Aquí guardaremos los resultados de la base de datos
    if conn:
        try:
            cursor = conn.cursor()
            # Primero, podrías limpiar los resultados anteriores para el modelo buscado
            
            # Luego, recupera los resultados de la base de datos para el modelo buscado
            
            # *******************************************************************
            # MODIFICACIÓN SOLICITADA EN LA SENTENCIA SQL:
            # Ahora seleccionamos 'marca' y 'modelo', y filtramos por 'marca' Y 'modelo'
            cursor.execute(
                "SELECT tienda, url, precio, imagen, titulo, marca, modelo FROM productos WHERE marca LIKE %s AND modelo LIKE %s",
                ('%' + marca + '%', '%' + modelo + '%',)
            )
            # *******************************************************************
            
            column_names = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                resultados_db.append(dict(zip(column_names, row)))

        except Exception as err:
            print("❌ Error al insertar/consultar datos:", err)
        finally:
            cursor.close()
            conn.close()

    response = jsonify(resultados_db)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
