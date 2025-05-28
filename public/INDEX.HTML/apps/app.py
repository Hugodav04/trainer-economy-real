from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

df = pd.read_csv('urls_zapatillas.csv')

@app.route('/')
def index():
    return render_template('index.html')  # tu página principal

@app.route('/buscar', methods=['POST'])
def buscar():
    marca = request.form.get('marca')
    modelo = request.form.get('modelo')

    # Filtrar el DataFrame por marca y modelo
    resultados = df.copy()
    if marca:
        resultados = resultados[resultados['marca'] == marca]
    if modelo:
        resultados = resultados[resultados['modelo'] == modelo]

    # Convertir a lista de diccionarios
    resultados_dict = resultados.to_dict(orient='records')

    return render_template('resultados.html', resultados=resultados_dict)

# Configuración de Chrome en modo headless
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
 
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
 
# URLs de producto actualizadas
urls = {
    "courir": "https://www.courir.es/es/p/nike-air-max-tl-2.5-chrome-1602190.html",
    "jdsports": "https://www.jdsports.es/product/gris-nike-air-max-tl-25/19683934_jdsportses/",
    "zalando": "https://www.zalando.es/nike-sportswear-air-max-unisex-zapatillas-whitevarsity-maizemidnight-navywolf-greyblack-ni115p000-a11.html",
    "footlocker": "https://www.footlocker.es/es/product/nike-air-max-tl-2-5-hombre-zapatillas/314217215004.html"
}
 
def obtener_precio(url):
    print(f"\n🔗 Visitando: {url}")
    try:
        driver.get(url)
        #time.sleep(3)  # Ya no es tan necesario con el timeout del driver y las esperas explícitas
 
        if "courir" in url:
            try:
                precio_elemento = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".product-price-container .price"))
                )
                return precio_elemento.text
            except:
                precio_elemento = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".default-price"))
                )
                return precio_elemento.text
 
        elif "jdsports" in url:
            precio_elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.pri[data-e2e='product-price']"))
            )
            return precio_elemento.text
 
        elif "zalando" in url:
            try:
                precio_elemento = WebDriverWait(driver, 15).until(  # Aumentamos el tiempo de espera para Zalando
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='price']"))
                )
                return precio_elemento.text
            except Exception as e:
                return f"❌ Error al obtener precio en Zalando (Timeout u otro): {e}"
 
        elif "footlocker" in url:
            precio_elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductPrice > span"))
            )
            return precio_elemento.text
 
        else:
            return "❌ Sitio no reconocido"
 
    except Exception as e:
        return f"❌ Error general al obtener precio: {e}"
 
# Ejecutar para cada tienda
for tienda, url in urls.items():
    precio = obtener_precio(url)
    print(f"💰 Precio en {tienda}: {precio}")
 
driver.quit()