
import time
import random
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import mysql.connector
 
 
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
    ua_list = os.getenv("USER_AGENTS")
    if ua_list:
        user_agents = ua_list.split(";")
    else:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
 
 
def scrape_eci(modelo, driver):
    q = modelo.replace(" ", "+")
    url = f"https://www.elcorteingles.es/deportes/search-nwx/1/?s={q}&stype=text_box"
    driver.get(url)
    time.sleep(1)
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
        ).click()
    except:
        pass
    enlace = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.product_link.pointer"))
    ).get_attribute("data-url")
    precio = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span.price-unit--normal"))
    ).text.strip().replace("\xa0", " ")
    img_elem = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img.js_preview_image"))
    )
    imagen = img_elem.get_attribute("src")
    title_elem = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.product_preview-title"))
    )
    titulo = title_elem.get_attribute("title").strip()
    return enlace, precio, imagen, titulo
 
 
def scrape_footlocker(modelo, driver):
    q = modelo.replace(" ", "+")
    url = f"https://www.footlocker.es/es/search?query={q}"
    driver.get(url)
    time.sleep(1)
    tarjeta = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.ProductCard-link.ProductCard-content"))
    )
    enlace = tarjeta.get_attribute("href")
    precio = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductPrice > span"))
    ).text.strip()
    driver.execute_script("arguments[0].scrollIntoView(true);", tarjeta)
    time.sleep(0.5)
    imagen = None
    try:
        img_elem = tarjeta.find_element(By.CSS_SELECTOR, "div.ProductCard-image img")
        imagen = img_elem.get_attribute("src") or img_elem.get_attribute("data-src")
    except NoSuchElementException:
        imagen = None
    try:
        title_elem = tarjeta.find_element(By.CSS_SELECTOR, "span.ProductName-primary")
        titulo = title_elem.text.strip()
    except NoSuchElementException:
        titulo = None
    return enlace, precio, imagen, titulo
 
 
def scrape_courir(modelo, driver):
    q = modelo.replace(" ", "+")
    url = f"https://www.courir.es/es/search?q={q}&lang=es_ES"
    driver.get(url)
    time.sleep(1)
    producto = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.product__link.js-product-link"))
    )
    href = producto.get_attribute("href")
    if not href.startswith("http"):
        href = "https://www.courir.es" + href
    precio = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-update-key='defaultPrice']"))
    ).text.strip().replace("\xa0", " ")
    img_elem = producto.find_element(By.TAG_NAME, "img")
    imagen = img_elem.get_attribute("src")
    title_elem = producto.find_element(By.CSS_SELECTOR, "div.product__details h3.product__name")
    titulo = title_elem.text.strip()
    return href, precio, imagen, titulo
 
 
def scrape_footdistrict(modelo, driver):
    q = modelo.replace(" ", "+")
    url = f"https://footdistrict.com/#c609/fullscreen/m=and&q={q}"
    driver.get(url)
    time.sleep(1)
    card = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.dfd-card.dfd-card-preset-product.dfd-card-type-feed_es"))
    )
    precio = card.find_element(By.CSS_SELECTOR, "span.dfd-card-price").text.strip().replace("\xa0", " ")
    enlace = card.get_attribute("dfd-value-link")
    img_elem = card.find_element(By.CSS_SELECTOR, "div.dfd-card-thumbnail img")
    imagen = img_elem.get_attribute("src")
    title_elem = card.find_element(By.CSS_SELECTOR, "div.dfd-card-title")
    titulo = title_elem.get_attribute("title") or title_elem.text.strip()
    return enlace, precio, imagen, titulo
 
 
# Utilidad para limpiar precios
def limpiar_precio(precio_raw):
    if not precio_raw:
        return "No disponible"
    precio = precio_raw.replace("€", "").replace(",", ".").strip()
    return precio if precio else "No disponible"
 
 
if __name__ == "__main__":
    modelo = input("Introduce el modelo de zapatillas: ").strip()
    driver = setup_driver(headless=True)
    resultados = []
    IMAGEN_POR_DEFECTO = "https://via.placeholder.com/150?text=No+Image"
 
    try:
        for tienda, func in [
            ("El Corte Inglés", scrape_eci),
            ("FootLocker", scrape_footlocker),
            ("Courir", scrape_courir),
            ("FootDistrict", scrape_footdistrict)
        ]:
            try:
                enlace, precio, imagen, titulo = func(modelo, driver)
                precio_limpio = limpiar_precio(precio)
                imagen_final = imagen if imagen else IMAGEN_POR_DEFECTO
                titulo_final = titulo if titulo else modelo
 
                resultados.append({
                    "Tienda": tienda,
                    "URL": enlace,
                    "Precio": precio_limpio,
                    "Imagen": imagen_final,
                    "Titulo": titulo_final
                })
                print(f"{tienda} → {enlace} → {precio_limpio} → {imagen_final} → {titulo_final}")
            except Exception as e:
                resultados.append({
                    "Tienda": tienda,
                    "URL": None,
                    "Precio": f"Error: {e}",
                    "Imagen": IMAGEN_POR_DEFECTO,
                    "Titulo": modelo
                })
                print(f"{tienda} Error: {e}")
    finally:
        driver.quit()
 
    # Guardar CSV
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo = f"resultados_{fecha}.csv"
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Tienda", "URL", "Precio", "Imagen", "Titulo"])
        writer.writeheader()
        writer.writerows(resultados)
    print(f"\n✅ Resultados guardados en {archivo}")
 
    # Guardar en MySQL
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3307,
            user="root",
            
            database="trainers"
        )
        cursor = conexion.cursor()
 
        for item in resultados:
            if item.get("URL") and not item["Precio"].startswith("Error"):
                cursor.execute("""
                    INSERT INTO productos (tienda, url, precio, imagen, titulo)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    item["Tienda"],
                    item["URL"],
                    item["Precio"],
                    item["Imagen"],
                    item["Titulo"]
                ))
 
        conexion.commit()
        print("✅ Resultados también guardados en la base de datos MySQL")
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar o insertar en MySQL: {err}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()