import os
import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

COOKIES_DIR = "cookies"
URL_SITE = "https://pi.equatorialenergia.com.br/sua-conta/"

def carregar_dados_sessao(driver, cnpj):
    """Carrega cookies, localStorage e sessionStorage"""
    cookie_path = os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json")
    local_storage_path = os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json")
    session_storage_path = os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json")

    if not os.path.exists(cookie_path):
        print(f"Nenhum dado de sessão encontrado para o CNPJ {cnpj}.")
        return False

    # Carregar cookies
    with open(cookie_path, "r") as file:
        cookies = json.load(file)
    for cookie in cookies:
        driver.add_cookie(cookie)

    print("Cookies carregados com sucesso!")

    # Carregar localStorage
    if os.path.exists(local_storage_path):
        with open(local_storage_path, "r") as file:
            local_storage_data = json.load(file)
        for key, value in local_storage_data.items():
            driver.execute_script(f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)});")

    # Carregar sessionStorage
    if os.path.exists(session_storage_path):
        with open(session_storage_path, "r") as file:
            session_storage_data = json.load(file)
        for key, value in session_storage_data.items():
            driver.execute_script(f"sessionStorage.setItem({json.dumps(key)}, {json.dumps(value)});")

    print("Local Storage e Session Storage carregados!")

    return True

def testar_sessao():
    """Abre o site e tenta restaurar a sessão"""
    cnpj = input("Digite o CNPJ: ").strip().replace(".", "").replace("/", "").replace("-", "")

    options = Options()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(URL_SITE)
    time.sleep(2)

    if carregar_dados_sessao(driver, cnpj):
        driver.refresh()
        time.sleep(2)
        print("Verifique se a sessão foi restaurada!")

    input("Pressione ENTER para fechar o navegador...")
    driver.quit()

if __name__ == "__main__":
    testar_sessao()
