from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configurações do Selenium
options = Options()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Inicializa o WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

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

        # Aguarda carregar as faturas
        wait.until(EC.presence_of_element_located((By.XPATH, "//tr[contains(@data-numero-fatura, '')]")))

        # Coleta as cinco últimas faturas disponíveis
        faturas = driver.find_elements(By.XPATH, "//tr[contains(@data-numero-fatura, '')]")[:5]

        for i, fatura in enumerate(faturas):
            try:
                botao_ver_fatura = fatura.find_element(By.XPATH, ".//a[contains(text(), 'Ver Fatura')]")
                botao_ver_fatura.click()
                print(f"Fatura {i+1} selecionada.")

                time.sleep(5)

            except Exception as e:
                print(f"Erro ao baixar fatura {i+1}: {e}")

        print("Download das 5 últimas faturas concluído.")

except Exception as e:
    print(f"Erro geral: {e}")

finally:
    driver.quit()
    print("Navegador fechado.")
