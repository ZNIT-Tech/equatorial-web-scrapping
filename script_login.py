import os
import json
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Diretório onde os cookies serão armazenados
COOKIES_DIR = "cookies"
URL_SITE = "https://pi.equatorialenergia.com.br/sua-conta/"  # URL do site

def salvar_dados_sessao(driver, cnpj):
    """Salva cookies, localStorage e sessionStorage"""
    if not os.path.exists(COOKIES_DIR):
        os.makedirs(COOKIES_DIR)

    # Salvar cookies
    cookies = driver.get_cookies()
    with open(os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json"), "w") as file:
        json.dump(cookies, file)

    # Salvar localStorage
    local_storage = driver.execute_script("return JSON.stringify(localStorage);")
    with open(os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json"), "w") as file:
        file.write(local_storage)

    # Salvar sessionStorage
    session_storage = driver.execute_script("return JSON.stringify(sessionStorage);")
    with open(os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json"), "w") as file:
        file.write(session_storage)

    print(f"Dados de sessão salvos para o CNPJ {cnpj}.")

def iniciar_login():
    """Abre o navegador para login manual e salva os dados da sessão"""
    cnpj = input("Digite o CNPJ: ").strip().replace(".", "").replace("/", "").replace("-", "")

    options = Options()
    options.add_argument("--start-maximized")  # Maximiza a janela
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(URL_SITE)
    input("Faça login manualmente e depois pressione ENTER no terminal...")

    salvar_dados_sessao(driver, cnpj)

    driver.quit()

if __name__ == "__main__":
    iniciar_login()
