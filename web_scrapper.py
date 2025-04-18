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
import zipfile

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

# Função para adaptar os cookies do Playwright para o formato do Selenium
def ajustar_cookies_playwright_para_selenium(cookies_playwright):
    cookies_selenium = []
    for cookie in cookies_playwright:
        novo_cookie = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie.get("path", "/"),
            "secure": cookie.get("secure", False),
            "httpOnly": cookie.get("httpOnly", False),
        }
        if "expires" in cookie and cookie["expires"] != -1:
            novo_cookie["expiry"] = int(cookie["expires"])
        cookies_selenium.append(novo_cookie)
    return cookies_selenium


# Gerando os meses aceitos
meses_aceitos = gerar_ultimos_5_meses()
print("Últimos 5 meses aceitos:", meses_aceitos)

# Definindo o diretório para downloads, usando variável de ambiente ou padrão
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/app/download')

# Função para carregar dados da sessão
def carregar_dados_sessao(driver, cnpj):
    cookie_path = os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json")
    local_storage_path = os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json")
    session_storage_path = os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json")

    if not os.path.exists(cookie_path):
        print(f"Nenhum dado de sessão encontrado para o CNPJ {cnpj}.")
        return False

    with open(cookie_path, "r") as file:
        cookies_playwright = json.load(file)

    cookies_selenium = ajustar_cookies_playwright_para_selenium(cookies_playwright)

    for cookie in cookies_selenium:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Erro ao adicionar cookie {cookie['name']}: {e}")

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

        time.sleep(20)
        driver.refresh()
        print("Página recarregada.")
        
        wait = WebDriverWait(driver, 30)

        # Fechar o banner de consentimento se estiver visível
        try:
            consent_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            consent_button.click()
            print("Consentimento aceito!")
        except:
            print("Banner de consentimento não encontrado ou já fechado.")

        # Verificar se há faturas disponíveis
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

            faturas_disponiveis = []
            for fatura in faturas:
                try:
                    mes_ano_fatura = fatura.find_element(By.XPATH, ".//span[@class='referencia_legada']").text.strip()
                    faturas_disponiveis.append((mes_ano_fatura, fatura))
                except:
                    continue

            # Ordenar as faturas do mais recente para o mais antigo
            faturas_disponiveis.sort(key=lambda x: datetime.strptime(x[0], "%m/%Y"), reverse=True)

            contagem = 0
            for mes_ano_fatura, fatura in faturas_disponiveis:
                if contagem >= 5:  # Se já baixou 5, para
                    print("Já baixei 5 faturas. Encerrando loop.")
                    break

                try:
                    print(f"Baixando fatura de {mes_ano_fatura}...")

                    tr_element = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//tr[.//span[contains(@class, 'referencia_legada') and text()='{mes_ano_fatura}']]")
                    ))
                    
                    # Rolando até o elemento antes de clicar
                    driver.execute_script("arguments[0].scrollIntoView();", tr_element)
                    time.sleep(1)  # Pequena pausa antes do clique
                    tr_element.click()
                    print("Elemento <tr> clicado com sucesso!")

                    botao_ver_fatura = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ver Fatura')]")))
                    botao_ver_fatura.click()

                    print(f"Fatura de {mes_ano_fatura} baixada com sucesso.")
                    time.sleep(3)

                    # Fechar modal **depois** de baixar a fatura
                    try:
                        botao_fechar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-close')]/i[contains(@class, 'fa fa-times')]")))
                        botao_fechar.click()
                        print("Botão de fechar clicado com sucesso!")
                    except:
                        print("Erro ao fechar modal, tentando forçar fechamento...")
                        driver.execute_script("document.querySelector('.modal-outter').style.display = 'none';")

                    contagem += 1
                    print(f"Contagem atual: {contagem}")

                except Exception as e:
                    print(f"Erro ao baixar fatura de {mes_ano_fatura}: {e}")

        time.sleep(10)
    except Exception as e:
        print(f"Erro geral: {e}")
    finally:
        print("Processo finalizado.")


# Função principal para testar a sessão
def testar_sessao(cnpj):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
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
    driver.quit()

    return True

def zip_pdfs(diretorio_downloads, nome_zip="faturas.zip"):
    arquivos_pdf = [f for f in os.listdir(diretorio_downloads) if f.endswith(".pdf")]

    if not arquivos_pdf:
        print("Nenhum arquivo PDF encontrado para compactar.")
        return None  # Evita retornar um caminho inválido

    zip_path = os.path.join(diretorio_downloads, nome_zip)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for arquivo in arquivos_pdf:
            caminho_completo = os.path.join(diretorio_downloads, arquivo)
            zipf.write(caminho_completo, os.path.basename(caminho_completo))

    return zip_path


def limpar_diretorio(diretorio):
    """Remove todos os arquivos dentro do diretório."""
    for arquivo in os.listdir(diretorio):
        caminho_arquivo = os.path.join(diretorio, arquivo)
        try:
            if os.path.isfile(caminho_arquivo) or os.path.islink(caminho_arquivo):
                os.unlink(caminho_arquivo)  # Remove arquivos e links simbólicos
            elif os.path.isdir(caminho_arquivo):
                os.rmdir(caminho_arquivo)  # Remove diretórios vazios (caso existam)
        except Exception as e:
            print(f"Erro ao apagar {caminho_arquivo}: {e}")
            
if __name__ == "__main__":
    testar_sessao()
