from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# Configurações do Selenium
options = Options()
#options.add_argument("--headless")  # Executa sem abrir a janela do navegador
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

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
    time.sleep(60)  # Espera 5 segundos
except Exception as e:
    print(f"Erro ao clicar no botão: {e}")

# Fecha o navegador
driver.quit()

# Requirements
# Instale as dependências necessárias com o comando:
# pip install selenium webdriver-manager
