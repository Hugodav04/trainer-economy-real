import time
import os
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, request, jsonify
from flask_cors import CORS  # Importa CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para permitir solicitudes desde tu dominio HTML

def setup_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-infobars")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--accept-language=es-ES,es;q=0.9")
    prefs = {"profile.managed_default_content_settings.images": 2}  # Deshabilita la carga de imágenes
    options.add_experimental_option("prefs", prefs)
    ua_list = os.getenv("USER_AGENTS")
    if ua_list:
        user_agents = ua_list.split(";")
    else:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def scrape_eci(modelo, driver):
    q_modelo = modelo.replace(" ", "+")
    url = f"https://www.elcorteingles.es/search-nwx/1/?s=zapatillas+hombre+{q_modelo}&stype=text_box"
    driver.get(url)
    try:
        WebDriverWait(driver, 3).until(  # Reducción del tiempo de espera
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
        ).click()
    except:
        pass
    try:
        enlace = WebDriverWait(driver, 7).until(  # Reducción del tiempo de espera
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.product_link.pointer"))
        ).get_attribute("data-url")
        precio = WebDriverWait(driver, 7).until(  # Reducción del tiempo de espera
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.price-unit--normal"))
        ).text.strip().replace("\xa0", " ")
        img_elem = WebDriverWait(driver, 7).until(  # Reducción del tiempo de espera
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.js_preview_image"))
        )
        imagen = img_elem.get_attribute("src")
        title_elem = WebDriverWait(driver, 7).until(  # Reducción del tiempo de espera
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.product_preview-title"))
        )
        titulo = title_elem.get_attribute("title").strip()
        return {"url": enlace, "precio": precio, "imagen": imagen, "titulo": titulo}
    except Exception as e:
        return {"error": str(e)}


def scrape_footlocker(modelo, driver):
    q_modelo = modelo.replace(" ", "+")
    url = f"https://www.footlocker.es/es/category/hombre/zapatillas.html?query={q_modelo}"
    driver.get(url)
    try:
        # Selector más específico para evitar resultados de bebé
        tarjeta = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductCard-content > a.ProductCard-link[href*='/product/']"))
        )
        enlace = tarjeta.get_attribute("href")
        precio = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductPrice > span"))
        ).text.strip()
        driver.execute_script("arguments[0].scrollIntoView(true);", tarjeta)
        time.sleep(0.1) # Reducción aún mayor
        imagen = None
        try:
            img_elem = tarjeta.find_element(By.CSS_SELECTOR, "div.ProductCard-image img")
            imagen = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")
        except NoSuchElementException:
            imagen = None
        titulo = None
        try:
            title_elem = tarjeta.find_element(By.CSS_SELECTOR, "span.ProductName-primary")
            titulo = title_elem.text.strip()
        except NoSuchElementException:
            titulo = None
        return {"url": enlace, "precio": precio, "imagen": imagen, "titulo": titulo}
    except Exception as e:
        return {"error": str(e)}


def scrape_courir(modelo, driver):
    q_modelo = modelo.replace(" ", "+")
    url = f"https://www.courir.es/es/c/hombre/?q={q_modelo}&lang=es_ES"
    driver.get(url)
    try:
        producto = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.product__link.js-product-link"))
        )
        href = producto.get_attribute("href")
        if not href.startswith("http"):
            href = "https://www.courir.es" + href
        precio = WebDriverWait(driver, 4).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-update-key='defaultPrice']"))
        ).text.strip().replace("\xa0", " ")
        img_elem = producto.find_element(By.TAG_NAME, "img")
        imagen = img_elem.get_attribute("src")
        title_elem = producto.find_element(By.CSS_SELECTOR, "div.product__details h3.product__name")
        titulo = title_elem.text.strip()
        return {"url": href, "precio": precio, "imagen": imagen, "titulo": titulo}
    except Exception as e:
        return {"error": str(e)}


def scrape_footdistrict(modelo, driver):
    url_to_test = "https://footdistrict.com/zapatillas/f/g/hombre/"
    driver.get(url_to_test)
    try:
        # Selector para la lista de productos (puede que necesites ajustarlo)
        lista_productos = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.dfd-card.dfd-card-preset-product.dfd-card-type-feed_es[dfd-value-link]"))
        )
        if lista_productos:
            # Si se encuentran productos, toma el enlace del primero como ejemplo
            primer_producto = lista_productos[0]
            enlace = primer_producto.get_attribute("dfd-value-link")
            precio_elem = primer_producto.find_element(By.CSS_SELECTOR, "span.dfd-card-price")
            precio = precio_elem.text.strip().replace("\xa0", " ")
            img_elem = primer_producto.find_element(By.CSS_SELECTOR, "div.dfd-card-thumbnail img")
            imagen = img_elem.get_attribute("src")
            title_elem = primer_producto.find_element(By.CSS_SELECTOR, "div.dfd-card-title")
            titulo = title_elem.get_attribute("title") if title_elem.get_attribute("title") else title_elem.text.strip()
            return {"url": enlace, "precio": precio, "imagen": imagen, "titulo": titulo}
        else:
            return {"error": "No se encontraron productos en la página."}
    except Exception as e:
        return {"error": f"Error al obtener datos de Footdistrict: {str(e)}"}


@app.route('/buscar_zapatillas', methods=['GET'])
def buscar_zapatillas():
    marca = request.args.get('marca')
    modelo = request.args.get('modelo')

    if not marca or not modelo:
        return jsonify({"error": "Debes proporcionar la marca y el modelo."}), 400

    driver = setup_driver(headless=True)
    resultados = {}
    try:
        for tienda, func in [
            ("El Corte Inglés", scrape_eci),
            ("FootLocker", scrape_footlocker),
            ("Courir", scrape_courir),
            ("FootDistrict", scrape_footdistrict)
        ]:
            resultados[tienda] = func(f"{marca} {modelo}", driver)
    finally:
        driver.quit()

    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)