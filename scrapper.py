from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
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

# Abre a página da Equatorial Energia
driver.get("https://www.equatorialenergia.com.br/")

# Obtém o título da página
titulo_pagina = driver.title
print(f"Título da página: {titulo_pagina}")

# Aguarda o botão aparecer e clica nele
try:
    wait = WebDriverWait(driver, 10)
    botao_piaui = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'PIAUÍ')]")))
    botao_piaui.click()
    print("Botão do Piauí clicado com sucesso.")
    
    # Aguarda e clica no botão de aceitar cookies
    botao_cookies = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
    botao_cookies.click()
    print("Botão de cookies clicado com sucesso.")
    
    # Aguarda e clica no botão "Continuar no site"
    botao_continuar = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continuar no site')]")))
    botao_continuar.click()
    print("Botão 'Continuar no site' clicado com sucesso.")
    
    # Aguarda e marca o checkbox "aviso_aceite"
    checkbox_aviso = wait.until(EC.element_to_be_clickable((By.ID, "aviso_aceite")))
    checkbox_aviso.click()
    print("Checkbox 'aviso_aceite' marcado com sucesso.")
    
    # Aguarda e clica no botão "Enviar"
    botao_enviar = wait.until(EC.element_to_be_clickable((By.ID, "lgpd_accept")))
    botao_enviar.click()
    print("Botão 'Enviar' clicado com sucesso.")
    
    # Aguarda e preenche o campo CPF/CNPJ caractere por caractere
    campo_cpf = wait.until(EC.element_to_be_clickable((By.ID, "identificador-otp")))
    cnpj = "06.626.253/0091-08"

    for char in cnpj:
        campo_cpf.send_keys(char)
        time.sleep(0.1)  # Pequeno delay para evitar falhas de digitação

    print("CNPJ inserido com sucesso caractere por caractere.")

    # Pressiona a seta para a esquerda uma vez
    campo_cpf.send_keys(Keys.ARROW_LEFT)
    print("Seta para a esquerda pressionada.")

    
    # Aguarda e clica no botão "Entrar"
    botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador-otp")))
    botao_entrar.click()
    print("Botão 'Entrar' clicado com sucesso.")
    
    # Aguarda e preenche o campo de senha
    campo_senha = wait.until(EC.element_to_be_clickable((By.ID, "senha-identificador")))
    campo_senha.send_keys("paguemenos.ubm@enel.com")
    print("Senha inserida com sucesso.")

    time.sleep(10)  # Espera para observar o resultado

    botao_entrar = wait.until(EC.element_to_be_clickable((By.ID, "envia-identificador")))
    botao_entrar.click()
    print("Botão 'Entrar' clicado com sucesso.")

    time.sleep(15)  # Espera para observar o resultado

    driver.get("https://pi.equatorialenergia.com.br/sua-conta/emitir-segunda-via/")

    try:
        # Espera até que o <tr> da fatura esteja presente na página
        fatura = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//tr[@data-bill-value='R$ 706,11' and @data-numero-fatura='300032524124']")
        ))

        # Aqui você pode clicar no botão que está dentro do <tr>
        # Modifique esse XPath para localizar o botão correto
        botao_fatura = fatura.find_element(By.XPATH, ".//button[contains(text(), 'Pagar')]")
        botao_fatura.click()
        print("Botão da fatura clicado com sucesso.")
    
    except Exception as e:
        print(f"Erro ao interagir com os elementos: {e}")

    try:
        # Aguarda até que o elemento <tr> esteja clicável.
        wait = WebDriverWait(driver, 10)
        tr_element = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//tr[contains(@data-bill-value, '706,11') and @data-numero-fatura='300032524124']")
        ))
        
        # Clica no elemento <tr>
        tr_element.click()
        print("Elemento <tr> clicado com sucesso!")
        
    except Exception as e:
        print("Erro ao clicar no elemento:", e)

    try:
        wait = WebDriverWait(driver, 40)
        botao_ver_fatura = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ver Fatura')]")))
        botao_ver_fatura.click()
        print("Botão 'Ver Fatura' clicado com sucesso.")
    except Exception as e:
        print(f"Erro ao clicar no botão 'Ver Fatura': {e}")

    time.sleep(10)  # Espera para observar o resultado

except Exception as e:
    print(f"Erro ao interagir com os elementos: {e}")

# Fecha o navegador
driver.quit()
