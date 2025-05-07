import os
import json
import time
import tempfile
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import zipfile
from web_scrapper import ajustar_cookies_playwright_para_selenium, carregar_dados_sessao

COOKIES_DIR = "cookies"
URL_SITE = "https://pi.equatorialenergia.com.br/sua-conta/"
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/app/download')

# Função para carregar dados da sessão

def obter_faturas_usina(driver):
    """Acessa a página e retorna uma lista de faturas disponíveis."""
    try:
        time.sleep(1)
        driver.get("https://pi.equatorialenergia.com.br/sua-conta/emitir-segunda-via/")
        print("Página de faturas carregada.")

        time.sleep(20)
        driver.refresh()
        print("Página recarregada.")

        wait = WebDriverWait(driver, 30)

        # Fechar o banner de consentimento se necessário
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
            return []

        faturas = driver.find_elements(By.XPATH, "//table//tr[@data-numero-fatura]")

        if not faturas:
            print("Nenhuma fatura encontrada.")
            return []

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

        baixar_faturas_usina(driver, faturas_disponiveis)

    except Exception as e:
        print(f"Erro ao obter faturas: {e}")
        return []

def baixar_faturas_usina(driver, faturas_disponiveis, max_downloads=5):
    """Baixa as faturas disponíveis, até um limite máximo."""
    wait = WebDriverWait(driver, 30)
    contagem = 0

    for mes_ano_fatura, fatura in faturas_disponiveis:
        if contagem >= max_downloads:
            print("Já baixei o número máximo de faturas permitido. Encerrando.")
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

            botao_ver_fatura = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ver Fatura')]")))
            botao_ver_fatura.click()

            print(f"Fatura de {mes_ano_fatura} baixada com sucesso.")
            time.sleep(3)

            # Fechar modal após o download
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

    print("Processo de download finalizado.")


def processar_todas_contas(driver):
    """ Alterna entre as contas contrato e chama obter_faturas_usina para cada uma """
    wait = WebDriverWait(driver, 30)

    # Primeiro, tentar fechar qualquer popup/modal que possa estar na tela
    fechar_popups(driver)

    try:
        # Tentar buscar o select de forma segura
        select_element = wait.until(EC.presence_of_element_located((By.ID, "conta_contrato")))
        select = Select(select_element)
        total_opcoes = len(select.options)

        for index in range(total_opcoes):
            tentativa = 0
            sucesso = False

            # Tentativa de clicar no select até 3 vezes
            while tentativa < 3 and not sucesso:
                try:
                    # Recarregar o elemento select a cada iteração
                    select_element = wait.until(EC.presence_of_element_located((By.ID, "conta_contrato")))
                    select = Select(select_element)

                    # Scroll até o elemento para garantir visibilidade
                    driver.execute_script("arguments[0].scrollIntoView();", select_element)
                    time.sleep(1)

                    # Clicar no select para abrir as opções
                    select_element.click()
                    time.sleep(1)

                    # Selecionar a conta contrato pelo índice
                    select.select_by_index(index)
                    print(f"✔ Conta contrato alterada para: {select.first_selected_option.text}")

                    # Espera para garantir que a mudança seja processada
                    time.sleep(2)

                    obter_faturas_usina(driver)  # Chama a função para baixar as faturas
                    sucesso = True  # Se não ocorrer erro, marca como sucesso
                except Exception as e:
                    print(f"❌ Erro ao tentar alterar conta contrato: {e}")
                    tentativa += 1  # Aumenta a tentativa
                    if tentativa == 3:
                        print("❌ Não foi possível alternar a conta contrato após 3 tentativas.")
                        break  # Se 3 tentativas falharem, sai do loop

    except Exception as e:
        print(f"❌ Erro ao acessar o select de contas contrato: {e}")

    print("✅ Todas as contas contrato foram processadas.")

def fechar_popups(driver):
    """ Fecha pop-ups ou banners que possam estar bloqueando interações na página. """
    try:
        wait = WebDriverWait(driver, 5)

        # Verifica se o pop-up de cookies (ou qualquer modal) está presente
        popup = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ot-btn-container")))

        if popup.is_displayed():
            print("🛑 Fechando pop-up de cookies...")
            
            # Tenta clicar no botão de aceitar cookies
            try:
                botao_aceitar = popup.find_element(By.XPATH, "//button[contains(text(),'Aceitar')]")
                botao_aceitar.click()
                time.sleep(2)  # Aguarde um tempo para o pop-up fechar
                print("✅ Pop-up fechado.")
            except Exception:
                print("⚠ Não foi possível clicar no botão de aceitar.")

            # Verifica se ainda há bloqueio e tenta remover
            try:
                script = """
                var elem = document.querySelector('.ot-btn-container');
                if (elem) { elem.remove(); }
                """
                driver.execute_script(script)
                print("✅ Removendo overlay de cookies via JavaScript.")
            except Exception as e:
                print(f"⚠ Erro ao remover overlay via JS: {e}")

    except Exception:
        print("✅ Nenhum pop-up para fechar.")

# Função principal para testar a sessão
def testar_sessao_usina(cnpj):
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

        processar_todas_contas(driver)
    driver.quit()

    return True



            
if __name__ == "__main__":
    testar_sessao_usina()
