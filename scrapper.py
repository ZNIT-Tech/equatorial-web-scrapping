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

# Configurações do Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("prefs", {
    "download.default_directory": "/home/enzo/repositories/equatorial-web-scrapping/download",  # Defina o diretório de download
    "download.prompt_for_download": False,  # Impede a janela de confirmação de download
    "plugins.always_open_pdf_externally": True  # Impede que o PDF seja aberto no navegador
})

# Inicializa o WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# Função para gerar os últimos 5 meses no formato "MM/YYYY"
def gerar_ultimos_5_meses():
    meses_validos = []
    data_atual = datetime.now()
    
    for i in range(5):
        mes_ref = data_atual - timedelta(days=30 * i)
        meses_validos.append(mes_ref.strftime("%m/%Y"))

    return meses_validos

# Obtém os últimos 5 meses no formato correto
meses_aceitos = gerar_ultimos_5_meses()
print("Últimos 5 meses aceitos:", meses_aceitos)

try:
    # Acessa a página de login
    driver.get("https://www.equatorialenergia.com.br/")
    print("Página carregada.")

    # Clica no estado Piauí
    botao_piaui = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'PIAUÍ')]")))
    botao_piaui.click()
    print("Acessando Equatorial Piauí.")

    # Aceita os cookies
    botao_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    botao_cookies.click()
    print("Cookies aceitos.")

    # Clica em "Continuar no site"
    botao_continuar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar no site')]")))
    botao_continuar.click()
    print("Continuando no site.")

    # Marca o checkbox "aviso_aceite"
    checkbox_aviso = wait.until(EC.element_to_be_clickable((By.ID, "aviso_aceite")))
    checkbox_aviso.click()
    print("Aviso de aceite marcado.")

    # Clica no botão "Enviar"
    botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "lgpd_accept")))
    botao_enviar.click()
    print("Enviado aceite LGPD.")

    # Loop para tentar o login até ser bem-sucedido
    login_sucesso = False
    tentativas = 0
    max_tentativas = 5  # Define um limite de tentativas para evitar loops infinitos

    while not login_sucesso and tentativas < max_tentativas:
        tentativas += 1
        print(f"Tentativa de login #{tentativas}...")

        # Preenche o campo de CNPJ
        campo_cnpj = wait.until(EC.element_to_be_clickable((By.ID, "identificador-otp")))
        campo_cnpj.clear()
        cnpj = "06.626.253/0091-08"

        for char in cnpj:
            campo_cnpj.send_keys(char)
            time.sleep(0.1)

        print("CNPJ inserido.")

        # Pressiona seta para a esquerda
        campo_cnpj.send_keys(Keys.ARROW_LEFT)

        # Clica no botão "Entrar"
        botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador-otp")))
        botao_entrar.click()
        print("Primeiro botão 'Entrar' clicado.")

        # Preenche o campo de senha
        campo_senha = wait.until(EC.element_to_be_clickable((By.ID, "senha-identificador")))
        campo_senha.send_keys("paguemenos.ubm@enel.com")
        print("Senha inserida.")

        # Clica novamente em "Entrar"
        botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador")))
        botao_entrar.click()
        print("Segundo botão 'Entrar' clicado.")

        # Aguarda um pouco para verificar se o login foi bem-sucedido ou se o erro aparece
        time.sleep(5)

        # Verifica se o alerta de erro apareceu
        try:
            alerta = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Atenção')]")))
            print("Aviso de erro detectado! Recarregando a página e tentando novamente...")

            # Recarrega a página e aguarda para iniciar novamente
            driver.refresh()
            time.sleep(5)

        except:
            print("Login bem-sucedido!")
            login_sucesso = True  # Sai do loop

    if not login_sucesso:
        print("Falha no login após várias tentativas. Verifique as credenciais.")

    else:
        # Acessa a página de faturas após login bem-sucedido
        driver.get("https://pi.equatorialenergia.com.br/sua-conta/emitir-segunda-via/")
        print("Página de faturas carregada.")

        # Espera até que as faturas estejam visíveis
        wait.until(EC.presence_of_element_located((By.XPATH, "//table//tr")))

        # Seleciona todas as faturas disponíveis na página
        faturas = driver.find_elements(By.XPATH, "//table//tr[@data-numero-fatura]")

        if len(faturas) == 0:
            print("Nenhuma fatura encontrada.")
        else:
            print(f"Encontradas {len(faturas)} faturas.")
            
            contagem = 0

            for fatura in faturas:
                try:
                    # Captura o mês/ano da fatura
                    mes_ano_fatura = fatura.find_element(By.XPATH, ".//span[@class='referencia_legada']").text.strip()
                    print (mes_ano_fatura)

                    if mes_ano_fatura in meses_aceitos:
                        print(f"Baixando fatura de {mes_ano_fatura}...")
                        tr_element = wait.until(EC.element_to_be_clickable(
                                    (By.XPATH, f"//tr[.//span[contains(@class, 'referencia_legada') and text()='{mes_ano_fatura}']]")
                                ))
                                
                                # Clica no elemento <tr>
                        tr_element.click()
                        print("Elemento <tr> clicado com sucesso!")

                        # Encontra o botão de download dentro da linha da fatura
                        wait = WebDriverWait(driver, 40)
                        botao_ver_fatura = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ver Fatura')]")))
                        botao_ver_fatura.click()

                        print(f"Fatura de {mes_ano_fatura} baixada com sucesso.")
                        time.sleep(3)  # Pequeno intervalo para evitar sobrecarga no site

                        # Clica no botão de fechar (fa fa-times dentro de modal-close)
                        botao_fechar = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'modal-close')]/i[contains(@class, 'fa fa-times')]")))
                        botao_fechar.click()
                        print("Botão de fechar clicado com sucesso!")


                        contagem += 1
                        if contagem >= 5:
                            break  # Para após baixar 5 faturas válidas

                except Exception as e:
                    print(f"Erro ao baixar fatura de {mes_ano_fatura}: {e}")

        time.sleep(10)
except Exception as e:
    print(f"Erro geral: {e}")

finally:
    driver.quit()
    print("Navegador fechado.")
