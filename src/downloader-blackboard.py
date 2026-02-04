import os
import json
import time
import re
import requests
import pyotp
import getpass
import tkinter as tk
from tkinter import filedialog
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONSTANTES GLOBALES ---
BASE_URL = "https://ev.us.es"
API_MEMBERSHIPS = f"{BASE_URL}/learn/api/public/v1/users/me/courses"
HISTORY_FILENAME = "download_history.json" # Nombre del archivo, pero la ruta será dinámica

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_instrucciones():
    limpiar_pantalla()
    print("="*70)
    print("      🎓 DOWNLOADER EV US - GUI EDITION")
    print("="*70)
    print("📋 INSTRUCCIONES:")
    print("   Requerimientos:")
    print("     - Google Chrome (sesión iniciada)")
    print("     - Extensión: Authenticator (con código de EV añadido) -> https://chromewebstore.google.com/detail/authenticator/bhghoamapcdpbohphigoooaddinpkbai?hl=en-US&utm_source=ext_sidebar")
    print("   1. Introduce UVUS y Contraseña.")
    print("   2. Selecciona el archivo de copia de seguridad")
    print("     OJO -> Obtención archivo:")
    print("              - (Chrome) > Ajustes > Extensiones > Authenticator")
    print("              - Ajustes > Copia de seguridad / Backup > Descargar una copia de seguridad / Download Backup File")
    print("   3. Elige dónde guardar los apuntes.")
    print("      (El historial de descargas se guardará DENTRO de esa carpeta).")
    print("="*70)
    print("\n")

def seleccionar_archivo_grafico():
    print("📂 Abriendo ventana de selección de archivo...")
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    ruta_archivo = filedialog.askopenfilename(
        title="Selecciona el archivo de backup de Authenticator",
        filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
    )
    root.destroy()
    return ruta_archivo

def extraer_secreto(ruta_archivo):
    if not ruta_archivo: return None
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()

        if contenido.startswith("otpauth://"):
            try:
                parsed = urlparse(contenido)
                params = parse_qs(parsed.query)
                if 'secret' in params:
                    print("✅ ¡Clave secreta encontrada!")
                    return params['secret'][0]
            except: pass
        elif "{" in contenido:
            try:
                datos = json.loads(contenido)
                entradas = datos.get('data', []) if isinstance(datos, dict) else datos
                for entrada in entradas:
                    if 'secret' in entrada:
                        return entrada['secret']
            except: pass
        print("❌ Formato de archivo no reconocido.")
        return None
    except: return None

def solicitar_datos():
    mostrar_instrucciones()
    
    # 1. Credenciales
    uvus = input("1. Usuario UVUS: ").strip()
    while not uvus: uvus = input("   Usuario obligatorio: ").strip()

    print("2. Contraseña (Oculta):")
    password = getpass.getpass("   Password: ").strip()
    
    # 2. Token
    secret = None
    while not secret:
        print("\n3. Selecciona el archivo de backup...")
        ruta = seleccionar_archivo_grafico()
        if not ruta:
            print("   ⚠️ Debes seleccionar un archivo.")
            continue
        secret = extraer_secreto(ruta)
        if not secret:
            if input("   ❌ Fallo. ¿Reintentar? (s/n): ").lower() != 's': exit()

    # 3. Ruta
    default_path = os.path.join(os.getcwd(), "EV_Downloads")
    print(f"\n4. Ruta de descarga (Enter para: {default_path})")
    ruta = input("   Ruta: ").strip()
    if not ruta: ruta = default_path
    
    if not os.path.exists(ruta):
        try: os.makedirs(ruta)
        except: pass
            
    return uvus, password, secret, ruta

def get_windows_long_path(path):
    abs_path = os.path.abspath(path)
    if os.name == 'nt' and not abs_path.startswith('\\\\?\\'):
        return '\\\\?\\' + abs_path
    return abs_path

def sanitize_clean(name):
    if not name: return "sin_nombre"
    name = re.sub(r'\s*\(.*?\)', '', name)
    name = name.split('-Grado en')[0]
    name = name.split('-Doble Grado')[0]
    name = name.split('-Máster Universitario')[0]
    name = re.sub(r'[<>:"/\\|?*]', '', name).strip()
    return name.rstrip('. ')

# --- GESTIÓN DE HISTORIAL (AHORA DINÁMICO) ---
def load_history(download_folder):
    """Carga el historial desde la carpeta de descargas"""
    history_path = os.path.join(download_folder, HISTORY_FILENAME)
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                return set(json.load(f))
        except: pass
    return set()

def save_history(history_set, download_folder):
    """Guarda el historial en la carpeta de descargas"""
    history_path = os.path.join(download_folder, HISTORY_FILENAME)
    try:
        with open(history_path, 'w') as f:
            json.dump(list(history_set), f)
    except Exception as e:
        print(f"⚠️ Error guardando historial: {e}")

# --- MOTOR ---
def get_session(uvus, password, secret):
    print("\n⚙️  Iniciando motor invisible...")
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    session = requests.Session()

    try:
        print("🤖 [LOGIN] Conectando...")
        driver.get("https://ev.us.es/ultra/course")
        wait = WebDriverWait(driver, 15)

        try: wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='auth-saml']"))).click()
        except: pass

        print("🔑 [LOGIN] Autenticando...")
        wait.until(EC.visibility_of_element_located((By.ID, "edit-name"))).send_keys(uvus)
        driver.find_element(By.ID, "edit-pass").send_keys(password)
        driver.find_element(By.ID, "submit_ok").click()

        try:
            code_input = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "input2factor")))
            totp = pyotp.TOTP(secret)
            code_input.send_keys(totp.now())
            code_input.send_keys("\n")
        except: pass

        print("⏳ [LOGIN] Verificando sesión...")
        WebDriverWait(driver, 60).until(EC.url_contains("ultra/course"))
        time.sleep(3) 

        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])
        return session
    finally:
        driver.quit()

def download_attachment(session, url, save_path):
    try:
        long_path = get_windows_long_path(save_path)
        folder = os.path.dirname(long_path)
        os.makedirs(folder, exist_ok=True)

        with session.get(url, stream=True) as r:
            r.raise_for_status()
            with open(long_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except: return False

def process_folder(session, course_id, content_id, current_path, history):
    if content_id:
        url = f"{BASE_URL}/learn/api/public/v1/courses/{course_id}/contents/{content_id}/children"
    else:
        url = f"{BASE_URL}/learn/api/public/v1/courses/{course_id}/contents"

    try:
        r = session.get(url)
        if r.status_code != 200: return
        items = r.json().get('results', [])

        for item in items:
            title = sanitize_clean(item.get('title', 'SinNombre'))
            item_id = item['id']
            handler = item.get('contentHandler', {}).get('id', '')

            if handler == 'resource/x-bb-folder':
                process_folder(session, course_id, item_id, os.path.join(current_path, title), history)
            else:
                if item_id in history: continue
                try:
                    att_r = session.get(f"{BASE_URL}/learn/api/public/v1/courses/{course_id}/contents/{item_id}/attachments")
                    if att_r.status_code == 200:
                        atts = att_r.json().get('results', [])
                        for att in atts:
                            fname = sanitize_clean(att.get('fileName', title))
                            if "." not in fname[-5:]: fname += ".pdf"
                            
                            dlink = f"{BASE_URL}/learn/api/public/v1/courses/{course_id}/contents/{item_id}/attachments/{att['id']}/download"
                            print(f"   ⬇️  {fname}")
                            if download_attachment(session, dlink, os.path.join(current_path, fname)):
                                history.add(item_id)
                except: pass
    except: pass

def main():
    # 1. SETUP
    uvus, password, secret, download_dir = solicitar_datos()

    print(f"\n🚀 INICIANDO EN: {download_dir}")
    # PASAMOS LA RUTA PARA CARGAR EL HISTORIAL LOCAL DE ESA CARPETA
    history = load_history(download_dir)
    
    session = get_session(uvus, password, secret)

    print("📡 Obteniendo asignaturas...")
    r = session.get(API_MEMBERSHIPS)
    memberships = r.json().get('results', [])
    
    count = 0
    for member in memberships:
        if member.get('availability', {}).get('available') != 'Yes': continue
        
        cid = member['courseId']
        r_c = session.get(f"{BASE_URL}/learn/api/public/v1/courses/{cid}")
        real_name = sanitize_clean(r_c.json().get('name', 'Curso') if r_c.status_code == 200 else "Curso")
        
        count += 1
        print(f"\n🎓 [{count}] {real_name}")
        process_folder(session, cid, None, os.path.join(download_dir, real_name), history)

    # GUARDAMOS EL HISTORIAL EN LA CARPETA DE DESCARGA
    save_history(history, download_dir)
    print("\n✅ ¡Todo sincronizado!")
    input("Presiona ENTER para salir...")

if __name__ == "__main__":
    main()