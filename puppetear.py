import asyncio
from pyppeteer import launch
import time

async def login(client_cpf_cnpj, senha, max_tentativas=3):
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.goto("https://www.equatorialenergia.com.br/login")
    await page.waitForSelector("#identificador-otp")

    login_sucesso = False
    tentativas = 0
    
    while not login_sucesso and tentativas < max_tentativas:
        tentativas += 1
        print(f"Tentativa de login #{tentativas}...")
        
        # Preencher CPF/CNPJ
        await page.evaluate("document.getElementById('identificador-otp').value = ''")
        cnpj_cpf = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
        for char in cnpj_cpf:
            await page.type("#identificador-otp", char, delay=100)
        print("CNPJ inserido.")
        
        # Clicar no primeiro botão Entrar
        await page.click("#envia-identificador-otp")
        print("Primeiro botão 'Entrar' clicado.")
        await page.waitForTimeout(10000)

        # Preencher senha
        await page.waitForSelector("#senha-identificador")
        await page.type("#senha-identificador", senha, delay=100)
        print("Senha inserida.")
        await page.waitForTimeout(10000)

        # Clicar no segundo botão Entrar
        await page.click("#envia-identificador")
        print("Segundo botão 'Entrar' clicado.")
        await page.waitForTimeout(10000)

        # Verificar erro de login
        alerta = await page.querySelector("xpath=//span[contains(text(), 'Atenção')]")
        if alerta:
            print("Aviso de erro detectado! Recarregando a página e tentando novamente...")
            await page.reload()
            await page.waitForTimeout(5000)
        else:
            print("Login bem-sucedido!")
            login_sucesso = True

    if not login_sucesso:
        print("Falha no login após várias tentativas. Verifique as credenciais.")
    
    await browser.close()

# Substitua pelos seus dados
cpf_cnpj = "18299576000167"
senha = "gracaabreu10@hotmail.com"

asyncio.run(login(cpf_cnpj, senha))
