import os
import json
import time
import tempfile
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

COOKIES_DIR = "cookies"
URL_SITE = "https://pi.equatorialenergia.com.br/sua-conta/"
meses_aceitos = []  # Será gerado com a função abaixo

# Função para gerar os últimos 5 meses aceitos
def gerar_ultimos_5_meses():
    meses_validos = []
    data_atual = datetime.now()
    
    for i in range(5):
        mes_ref = data_atual - timedelta(days=30 * i)
        meses_validos.append(mes_ref.strftime("%m/%Y"))

    return meses_validos

# Gerando os meses aceitos
meses_aceitos = gerar_ultimos_5_meses()
print("Últimos 5 meses aceitos:", meses_aceitos)

# Definindo o diretório para downloads, usando variável de ambiente ou padrão
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Função para carregar dados da sessão
def carregar_dados_sessao(driver, cnpj):
    cookie_path = os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json")
    local_storage_path = os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json")
    session_storage_path = os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json")

    if not os.path.exists(cookie_path):
        print(f"Nenhum dado de sessão encontrado para o CNPJ {cnpj}.")
        return False

    with open(cookie_path, "r") as file:
        cookies = json.load(file)
    for cookie in cookies:
        driver.add_cookie(cookie)

    print("Cookies carregados com sucesso!")

    if os.path.exists(local_storage_path):
        with open(local_storage_path, "r") as file:
            local_storage_data = json.load(file)
        for key, value in local_storage_data.items():
            driver.execute_script(f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)});")

    if os.path.exists(session_storage_path):
        with open(session_storage_path, "r") as file:
            session_storage_data = json.load(file)
        for key, value in session_storage_data.items():
            driver.execute_script(f"sessionStorage.setItem({json.dumps(key)}, {json.dumps(value)});")

    print("Local Storage e Session Storage carregados!")

    return True

# Função para acessar a página de faturas e fazer o download
def acessar_faturas(driver):
    try:
        time.sleep(1)
        driver.get("https://pi.equatorialenergia.com.br/sua-conta/emitir-segunda-via/")
        print("Página de faturas carregada.")

        time.sleep(10)
        driver.refresh()
        print("Página recarregada.")
        
        time.sleep(100)
        wait = WebDriverWait(driver, 120)

        # Fechar o banner de consentimento se estiver visível
        try:
            consent_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            consent_button.click()
            print("Consentimento aceito!")
        except Exception as e:
            print("Banner de consentimento não encontrado ou já fechado.")
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//table//tr")))
        except TimeoutException:
            print("Tabela de faturas não encontrada dentro do tempo limite.")
            return

        faturas = driver.find_elements(By.XPATH, "//table//tr[@data-numero-fatura]")

        if len(faturas) == 0:
            print("Nenhuma fatura encontrada.")
        else:
            print(f"Encontradas {len(faturas)} faturas.")
            
            contagem = 0

            for fatura in faturas:
                try:
                    mes_ano_fatura = fatura.find_element(By.XPATH, ".//span[@class='referencia_legada']").text.strip()
                    print(mes_ano_fatura)

                    if mes_ano_fatura in meses_aceitos:
                        print(f"Baixando fatura de {mes_ano_fatura}...")
                        tr_element = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, f"//tr[.//span[contains(@class, 'referencia_legada') and text()='{mes_ano_fatura}']]")
                                ))
                                
                        tr_element.click()
                        print("Elemento <tr> clicado com sucesso!")

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
        print("Processo finalizado. Navegador fechado.")


# Função principal para testar a sessão
def testar_sessao():
    cnpj = input("Digite o CNPJ: ").strip().replace(".", "").replace("/", "").replace("-", "")

    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {
        "download.default_directory": "C:\\Users\\Enzo Roosch\\Documents\\Repositories\\equatorial-web-scrapping\\download",
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,
        "download.directory_upgrade": True,
    })

    # Criando um diretório temporário para os dados do usuário
    user_data_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={user_data_dir}")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(URL_SITE)
    time.sleep(2)

    if carregar_dados_sessao(driver, cnpj):
        driver.refresh()
        time.sleep(2)
        print("Verifique se a sessão foi restaurada!")

        acessar_faturas(driver)

    input("Pressione ENTER para fechar o navegador...")
    driver.quit()

if __name__ == "__main__":
    testar_sessao()
