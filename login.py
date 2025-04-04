import asyncio
import json
import os
import random
import time
from playwright.async_api import async_playwright

# Diretórios para armazenar cookies
COOKIES_DIR = "cookies"
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)

def random_delay(min_delay=1, max_delay=3):
    time.sleep(random.uniform(min_delay, max_delay))

async def save_Credentials(client_cpf_cnpj: str, senha: str, estado: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Altere para True se quiser rodar em segundo plano
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            accept_downloads=True
        )
        page = await context.new_page()

        try:
            # Acessa o site
            await page.goto("https://pi.equatorialenergia.com.br/")
            print("Página carregada.")

            # Aceitar cookies
            try:
                await page.locator("#onetrust-accept-btn-handler").click(timeout=5000)
                print("Cookies aceitos.")
            except:
                print("Nenhum botão de cookies encontrado.")

            random_delay()

            # Clicar em "Continuar no site"
            await page.locator("//button[contains(text(), 'Continuar no site')]").click()
            print("Continuando no site.")

            # Aceitar aviso LGPD
            await page.locator("#aviso_aceite").click()
            print("Aviso de aceite marcado.")

            await page.locator("#lgpd_accept").click()
            print("Enviado aceite LGPD.")

            random_delay()

            login_sucesso = False
            tentativas = 0
            max_tentativas = 5

            while not login_sucesso and tentativas < max_tentativas:
                tentativas += 1
                print(f"Tentativa de login #{tentativas}...")

                campo_cnpj_cpf = await page.wait_for_selector("#identificador-otp")

                # Remove caracteres especiais do CPF/CNPJ
                cnpj_cpf_limpo = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")

                # Digita um caractere por vez com um pequeno delay para simular digitação humana
                for char in cnpj_cpf_limpo:
                    await campo_cnpj_cpf.type(char, delay=100)  # Pequeno delay entre teclas
                print("CNPJ inserido caractere por caractere.")

                # Pressiona a seta para a esquerda
                await campo_cnpj_cpf.press("ArrowLeft")
                print("Seta para a esquerda pressionada.")

                random_delay()
                await page.locator("#envia-identificador-otp").click()
                print("Primeiro botão 'Entrar' clicado.")

                random_delay()

                # Preenche senha
                campo_senha = await page.wait_for_selector("#senha-identificador")
                await campo_senha.fill(senha)
                print("Senha inserida.")

                random_delay()
                await page.locator("#envia-identificador").click()
                print("Segundo botão 'Entrar' clicado.")

                time.sleep(15)  # Espera o carregamento da página

                # Verificar erro no login
                if await page.locator("//span[contains(text(), 'Atenção')]").is_visible():
                    print("Aviso de erro detectado! Recarregando a página e tentando novamente...")
                    await page.reload()
                    await asyncio.sleep(5)
                    continue  # Tentar novamente

                # Verifica se o login foi bem-sucedido pela URL
                if "/sua-conta/" in page.url:
                    print("Login bem sucedido!")
                    login_sucesso = True
                    break
                else:
                    print("Login não bem sucedido, tentando novamente...")
                    await page.reload()
                    await asyncio.sleep(5)

            if not login_sucesso:
                print("Falha no login após várias tentativas. Verifique as credenciais.")
                return

            # Salvar cookies
            cnpj = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
            cookies = await context.cookies()
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json"), "w") as file:
                json.dump(cookies, file)

            # Salvar localStorage
            local_storage = await page.evaluate("JSON.stringify(localStorage);")
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json"), "w") as file:
                file.write(local_storage)

            # Salvar sessionStorage
            session_storage = await page.evaluate("JSON.stringify(sessionStorage);")
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json"), "w") as file:
                file.write(session_storage)

            print("Cookies e storage salvos com sucesso.")

        except Exception as e:
            print(f"Erro geral: {e}")

        finally:
            await browser.close()
            print("Navegador fechado.")


