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
from dotenv import load_dotenv
import os
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

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

def parse_cookie_string(cookie_string):
    cookies = []
    for pair in cookie_string.split('; '):
        if '=' in pair:
            name, value = pair.split('=', 1)
            cookies.append({
                "name": name,
                "value": value,
                "domain": "pi.equatorialenergia.com.br",
                "path": "/",
                "secure": False,
                "httpOnly": False
            })
    return cookies

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

def buscar_sessao_por_cpf(cpf):
    response = supabase.table("credenciais_clientes").select("*").eq("cnpj_cpf", cpf).order("id", desc=True).limit(1).execute()
    if response.data:
        return response.data[0]
    return None

# Função para carregar dados da sessão
def carregar_dados_sessao(driver, cnpj):
    
    sessao = buscar_sessao_por_cpf(cnpj)  # ou buscar_sessao_por_cnpj
    if not sessao:
        print("⚠️ Nenhuma sessão encontrada no Supabase.")
        return False

    # Interações iniciais
    driver.get("https://pi.equatorialenergia.com.br/")
    time.sleep(2)
    
    try:
        cookies_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookies_button.click()
    except: pass

    # Aplicando cookies
    cookies_raw = sessao.get("cookies", "")
    cookies_list = parse_cookie_string(cookies_raw)
    for cookie in cookies_list:
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Erro ao aplicar cookie {cookie}: {e}")

    # LocalStorage
    if sessao.get("local_storage"):
        for key, value in sessao["local_storage"].items():
            driver.execute_script(f"localStorage.setItem('{key}', `{value}`);")

    # SessionStorage
    if sessao.get("session_storage"):
        for key, value in sessao["session_storage"].items():
            driver.execute_script(f"sessionStorage.setItem('{key}', `{value}`);")

    driver.get("https://pi.equatorialenergia.com.br/")
    time.sleep(3)
    print("✅ Sessão restaurada do Supabase.")
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
                    
                    driver.execute_script("arguments[0].scrollIntoView();", tr_element)
                    time.sleep(1)
                    tr_element.click()
                    print("Elemento <tr> clicado com sucesso!")

                    # Espera com múltiplas tentativas para o botão "Ver Fatura"
                    for tentativa in range(3):
                        try:
                            WebDriverWait(driver, 30).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "modal-outter"))
                            )
                            botao_ver_fatura = WebDriverWait(driver, 60).until(
                                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ver Fatura')]"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView();", botao_ver_fatura)
                            time.sleep(1)
                            botao_ver_fatura.click()
                            print(f"Fatura de {mes_ano_fatura} baixada com sucesso.")
                            break
                        except Exception as e:
                            print(f"Tentativa {tentativa + 1}/3 falhou ao clicar em 'Ver Fatura': {e}")
                            time.sleep(5)
                    else:
                        print(f"❌ Não foi possível clicar em 'Ver Fatura' para {mes_ano_fatura} após 3 tentativas.")
                        continue  # Pula para a próxima fatura

                    time.sleep(3)

                    # Fechar modal após baixar a fatura
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
