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
    options.add_argument("--enable-unsafe-swiftshader")
 
    ua_list = os.getenv("USER_AGENTS")
    user_agents = ua_list.split(";") if ua_list else [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."
    ]
    options.add_argument(f"--user-agent={random.choice(user_agents)}")
 
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
 
 
# -------------------------------
# Funciones de Scraping por tienda
# -------------------------------
 
def scrape_eci(modelo, driver):
    query = modelo.replace(" ", "+")
    driver.get(f"https://www.elcorteingles.es/deportes/search-nwx/1/?s={query}&stype=text_box")
    time.sleep(1)
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass
 
    enlace = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.product_link.pointer"))
    ).get_attribute("data-url")
    precio = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "span.price-unit--normal"))
    ).text.strip().replace("\xa0", " ")
    imagen = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img.js_preview_image"))
    ).get_attribute("src")
    titulo = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.product_preview-title"))
    ).get_attribute("title").strip()
 
    return enlace, precio, imagen, titulo
 
 
def scrape_footlocker(modelo, driver):
    driver.get(f"https://www.footlocker.es/es/search?query={modelo.replace(' ', '+')}")
    time.sleep(1)
 
    contenedor = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "li.product-container-mobile-v3"))
    )
 
    tarjeta = contenedor.find_element(By.CSS_SELECTOR, "a.ProductCard-link.ProductCard-content")
    enlace = tarjeta.get_attribute("href")
 
    precio = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProductPrice > span"))
    ).text.strip()
 
    imagen = IMAGEN_POR_DEFECTO
    try:
        img = contenedor.find_element(By.CSS_SELECTOR, "img.ProductCard-image--primary")
        imagen = (
            img.get_attribute("src")
            or img.get_attribute("data-src")
            or img.get_attribute("srcset")
            or img.get_attribute("data-srcset")
            or IMAGEN_POR_DEFECTO
        )
        if "," in imagen:
            imagen = imagen.split(",")[0].split(" ")[0]
    except Exception:
        pass
 
    try:
        titulo = contenedor.find_element(By.CSS_SELECTOR, "span.ProductName-primary").text.strip()
    except NoSuchElementException:
        titulo = modelo
 
    return enlace, precio, imagen, titulo
 
 
def scrape_courir(modelo, driver):
    driver.get(f"https://www.courir.es/es/search?q={modelo.replace(' ', '+')}&lang=es_ES")
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
 
    imagen = producto.find_element(By.TAG_NAME, "img").get_attribute("src")
    titulo = producto.find_element(By.CSS_SELECTOR, "div.product__details h3.product__name").text.strip()
 
    return href, precio, imagen, titulo
 
 
def scrape_footdistrict(modelo, _):
    driver = setup_driver(headless=True)
    try:
        driver.get(f"https://footdistrict.com/#c609/fullscreen/m=and&q={modelo.replace(' ', '+')}")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.dfd-card-title"))
        )
        time.sleep(1)
 
        cards = driver.find_elements(By.CSS_SELECTOR, "div.dfd-card.dfd-card-preset-product.dfd-card-type-feed_es")
        if not cards:
            raise Exception("❌ No se encontraron productos en FootDistrict.")
 
        card = cards[0]
        precio = card.find_element(By.CSS_SELECTOR, "span.dfd-card-price").text.strip().replace("\xa0", " ")
        enlace = card.get_attribute("dfd-value-link")
        if not enlace.startswith("http"):
            enlace = "https://footdistrict.com" + enlace
 
        imagen = card.find_element(By.CSS_SELECTOR, "div.dfd-card-thumbnail img").get_attribute("src")
        titulo = card.find_element(By.CSS_SELECTOR, "div.dfd-card-title").get_attribute("title")
 
        return enlace, precio, imagen, titulo or modelo
    finally:
        driver.quit()
 
 
 
def limpiar_precio(precio_raw):
    if not precio_raw:
        return "No disponible"
    return precio_raw.replace("€", "").replace(",", ".").strip() or "No disponible"
 
 
def guardar_csv(resultados, nombre_base="resultados"):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo = f"{nombre_base}_{fecha}.csv"
    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Tienda", "URL", "Precio", "Imagen", "Titulo", "Marca", "Modelo"])
        writer.writeheader()
        writer.writerows(resultados)
    print(f"\n✅ Resultados guardados en {archivo}")
 
 
def guardar_mysql(resultados):
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            port=3307,
            user="root",
            database="trainers"

        )
        cursor = conexion.cursor()
 
        for item in resultados:
            if item["URL"] and not item["Precio"].startswith("Error"):
                cursor.execute("""
                    INSERT INTO productos (tienda, url, precio, imagen, titulo, marca, modelo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    item["Tienda"], item["URL"], item["Precio"], item["Imagen"],
                    item["Titulo"], item["Marca"], item["Modelo"]
                ))
        conexion.commit()
        print("✅ Resultados también guardados en MySQL")
    except mysql.connector.Error as err:
        print(f"❌ Error MySQL: {err}")
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()
 
 
if __name__ == "__main__":
    marcas_modelos = {
        "NIKE": ["Air max 90", "Air force 1", "Dunk low", "Air pegasus","Zoom Vomero","Air Zoom"],
        "ASICS": ["GEL 1130", "GEL-NYC", "GEL-VENTURE 6", "GT-2160","Kinetic fluent","GEL-QUANTUM"],
        "ADIDAS": ["Campus 00s", "Gazelle", "Samba OG", "Handball spezial", "sl 72 rs"],
        "New Balance": ["9060", "530", "327",]
    }
 
    driver = setup_driver(headless=True)
    resultados = []
    IMAGEN_POR_DEFECTO = "https://via.placeholder.com/150?text=No+Image"
 
    try:
        for marca, modelos in marcas_modelos.items():
            for modelo in modelos:
                print(f"\n🔍 Buscando {marca} - {modelo}")
                for tienda, funcion_scraper in [
                    ("El Corte Inglés", scrape_eci),
                    ("FootLocker", scrape_footlocker),
                    ("Courir", scrape_courir),
                    ("FootDistrict", lambda modelo, _: scrape_footdistrict (modelo,None))
                ]:
                    try:
                        enlace, precio, imagen, titulo = funcion_scraper(modelo, driver)
                        resultados.append({
                            "Tienda": tienda,
                            "URL": enlace,
                            "Precio": limpiar_precio(precio),
                            "Imagen": imagen or IMAGEN_POR_DEFECTO,
                            "Titulo": titulo or modelo,
                            "Marca": marca,
                            "Modelo": modelo
                        })
                        print(f"{tienda} → {enlace} → {precio}")
                    except Exception as e:
                        resultados.append({
                            "Tienda": tienda,
                            "URL": None,
                            "Precio": f"Error: {e}",
                            "Imagen": IMAGEN_POR_DEFECTO,
                            "Titulo": modelo,
                            "Marca": marca,
                            "Modelo": modelo
                        })
                        print(f"{tienda} ❌ Error: {e}")
    finally:
        driver.quit()
 
    guardar_csv(resultados)
    guardar_mysql(resultados)