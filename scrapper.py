from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta
import os
import tempfile
import json

import os

# Define um diretório dentro do container
COOKIES_DIR = "cookies"
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")  # Usa variável de ambiente ou default
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Garante que o diretório existe
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

import random

def random_delay(min_delay=1, max_delay=3):
    time.sleep(random.uniform(min_delay, max_delay))


def scrape_data(client_cpf_cnpj: str, senha: str, estado: str):
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    #options.add_argument("--headless=new")  # Novo modo headless que permite downloads
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("Accept-Language: en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7")
    options.add_argument("Accept-Encoding: gzip, deflate, br")
    options.add_argument("Connection: keep-alive")
    options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_DIR,  # Caminho onde os arquivos serão baixados
    "download.prompt_for_download": False,  # Impede a janela de confirmação 
    "plugins.always_open_pdf_externally": True,  # Impede que o PDF seja aberto no navegador
    "safebrowsing.enabled": True,  # Habilita o download seguro
    "download.directory_upgrade": True,  # Força o Chrome a usar o diretório especificado
    })

    # Create a temporary directory for the user data to avoid conflicts
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://pi.equatorialenergia.com.br/")
        print("Página carregada.")
    

        botao_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        botao_cookies.click()
        print("Cookies aceitos.")

        random_delay()

        botao_continuar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar no site')]")))
        botao_continuar.click()
        print("Continuando no site.")

        checkbox_aviso = wait.until(EC.element_to_be_clickable((By.ID, "aviso_aceite")))
        checkbox_aviso.click()
        print("Aviso de aceite marcado.")

        botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "lgpd_accept")))
        botao_enviar.click()
        print("Enviado aceite LGPD.")
        random_delay()
        login_sucesso = False
        tentativas = 0
        max_tentativas = 5  # Define um limite de tentativas para evitar loops infinitos

        while not login_sucesso and tentativas < max_tentativas:
            tentativas += 1
            print(f"Tentativa de login #{tentativas}...")

            campo_cnpj_cpf = wait.until(EC.element_to_be_clickable((By.ID, "identificador-otp")))
            campo_cnpj_cpf.clear()
            cnpj_cpf = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")

            for char in cnpj_cpf:
                campo_cnpj_cpf.send_keys(char)
                random_delay()

            print("CNPJ inserido.")

            campo_cnpj_cpf.send_keys(Keys.ARROW_LEFT)

            botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador-otp")))
            botao_entrar.click()
            print("Primeiro botão 'Entrar' clicado.")
            
            random_delay()
            campo_senha = wait.until(EC.element_to_be_clickable((By.ID, "senha-identificador")))
            campo_senha.send_keys(f"{senha}")
            print("Senha inserida.")

            random_delay()
            botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador")))
            botao_entrar.click()
            print("Segundo botão 'Entrar' clicado.")

            random_delay()

            try:
                alerta = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Atenção')]")))
                print("Aviso de erro detectado! Recarregando a página e tentando novamente...")

                driver.refresh()
                time.sleep(5)

            except:
                print("Sem erros")

            try:
                # Aguarda a mudança da URL
                wait.until(EC.url_contains("/sua-conta/"))
                print("Login bem sucedido!")
                login_sucesso = True  # Sai do loop se a URL for a esperada
            except:
                print("Login não bem sucedido, tentando novamente...")
                driver.refresh()
                time.sleep(5)  # Espera antes de tentar novamente

        if not login_sucesso:
            print("Falha no login após várias tentativas. Verifique as credenciais.")

        else:
        
                cnpj = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
                print("Login bem sucedido")
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
    except Exception as e:
        print(f"Erro geral: {e}")

    finally:
        driver.quit()
        print("Navegador fechado.")

scrape_data("1137120304", "25/08/1985", "Piauí")