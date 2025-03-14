from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta
import os
import tempfile

import os

# Define um diretório dentro do container
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")  # Usa variável de ambiente ou default
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Garante que o diretório existe
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def scrape_data(client_cpf_cnpj: str, senha: str, estado: str):
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    options.add_argument("--headless=new")  # Novo modo headless que permite downloads
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
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
    wait = WebDriverWait(driver, 15)

    def gerar_ultimos_5_meses():
        meses_validos = []
        data_atual = datetime.now()
        
        for i in range(5):
            mes_ref = data_atual - timedelta(days=30 * i)
            meses_validos.append(mes_ref.strftime("%m/%Y"))

        return meses_validos

    meses_aceitos = gerar_ultimos_5_meses()
    print("Últimos 5 meses aceitos:", meses_aceitos)

    try:
        driver.get("https://www.equatorialenergia.com.br/")
        print("Página carregada.")

        botao_estado = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{estado}')]")))
        botao_estado.click()
        print("Acessando Equatorial Piauí.")

        botao_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        botao_cookies.click()
        print("Cookies aceitos.")

        botao_continuar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar no site')]")))
        botao_continuar.click()
        print("Continuando no site.")

        checkbox_aviso = wait.until(EC.element_to_be_clickable((By.ID, "aviso_aceite")))
        checkbox_aviso.click()
        print("Aviso de aceite marcado.")

        botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "lgpd_accept")))
        botao_enviar.click()
        print("Enviado aceite LGPD.")

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
                time.sleep(0.1)

            print("CNPJ inserido.")

            campo_cnpj_cpf.send_keys(Keys.ARROW_LEFT)

            botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador-otp")))
            botao_entrar.click()
            print("Primeiro botão 'Entrar' clicado.")
            
            time.sleep(10)
            campo_senha = wait.until(EC.element_to_be_clickable((By.ID, "senha-identificador")))
            campo_senha.send_keys(f"{senha}")
            print("Senha inserida.")

            time.sleep(10)
            botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador")))
            botao_entrar.click()
            print("Segundo botão 'Entrar' clicado.")

            time.sleep(10)

            try:
                alerta = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Atenção')]")))
                print("Aviso de erro detectado! Recarregando a página e tentando novamente...")

                driver.refresh()
                time.sleep(5)

            except:
                print("Login bem-sucedido!")
                login_sucesso = True  # Sai do loop

        if not login_sucesso:
            print("Falha no login após várias tentativas. Verifique as credenciais.")

        else:
            time.sleep(1)
            driver.get("https://pi.equatorialenergia.com.br/sua-conta/emitir-segunda-via/")
            print("Página de faturas carregada.")

            wait.until(EC.presence_of_element_located((By.XPATH, "//table//tr")))

            faturas = driver.find_elements(By.XPATH, "//table//tr[@data-numero-fatura]")

            if len(faturas) == 0:
                print("Nenhuma fatura encontrada.")
            else:
                print(f"Encontradas {len(faturas)} faturas.")
                
                contagem = 0

                for fatura in faturas:
                    try:
                        mes_ano_fatura = fatura.find_element(By.XPATH, ".//span[@class='referencia_legada']").text.strip()
                        print (mes_ano_fatura)

                        if mes_ano_fatura in meses_aceitos:
                            print(f"Baixando fatura de {mes_ano_fatura}...")
                            tr_element = wait.until(EC.element_to_be_clickable(
                                        (By.XPATH, f"//tr[.//span[contains(@class, 'referencia_legada') and text()='{mes_ano_fatura}']]")
                                    ))
                                    
                            tr_element.click()
                            print("Elemento <tr> clicado com sucesso!")

                            wait = WebDriverWait(driver, 120)
                            botao_ver_fatura = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ver Fatura')]")))
                            botao_ver_fatura.click()

                            print(f"Fatura de {mes_ano_fatura} baixada com sucesso.")
                            time.sleep(3)  

                            botao_fechar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-close')]/i[contains(@class, 'fa fa-times')]")))
                            botao_fechar.click()
                            print("Botão de fechar clicado com sucesso!")


                            contagem += 1
                            if contagem >= 5:
                                break  

                    except Exception as e:
                        print(f"Erro ao baixar fatura de {mes_ano_fatura}: {e}")

            time.sleep(10)
    except Exception as e:
        print(f"Erro geral: {e}")

    finally:
        driver.quit()
        print("Navegador fechado.")
