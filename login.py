import asyncio
import json
import os
import random
import time
from playwright.async_api import async_playwright

COOKIES_DIR = "cookies"
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)

user_agents = [
    "Mozilla/5.0 (iPad; CPU OS 8_4_1 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H321 Safari/600.1.4",
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240"
]

def random_delay(min_delay=1.5, max_delay=3.5):
    time.sleep(random.uniform(min_delay, max_delay))

async def save_Credentials(client_cpf_cnpj: str, senha: str, estado: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, slow_mo=80)  # mais natural
        context = await browser.new_context(
            #user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            user_agent=random.choice(user_agents),
            accept_downloads=True,
            viewport={"width": 1280, "height": 800},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        page = await context.new_page()
        try:
            await page.goto("https://pi.equatorialenergia.com.br/", timeout=60000)
            print("Página carregada.")

            try:
                await page.locator("#onetrust-accept-btn-handler").click(timeout=5000)
                print("Cookies aceitos.")
            except:
                print("Nenhum botão de cookies encontrado.")

            random_delay()
            await page.locator("//button[contains(text(), 'Continuar no site')]").click()
            print("Continuando no site.")

            await page.locator("#aviso_aceite").click()
            await page.locator("#lgpd_accept").click()
            print("Aviso e LGPD aceitos.")

            random_delay()

            login_sucesso = False
            tentativas = 0
            max_tentativas = 5

            while not login_sucesso and tentativas < max_tentativas:
                tentativas += 1
                print(f"Tentativa de login #{tentativas}...")

                campo_cnpj_cpf = await page.wait_for_selector("#identificador-otp", timeout=10000)
                cnpj_cpf_limpo = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")

                for char in cnpj_cpf_limpo:
                    await campo_cnpj_cpf.type(char, delay=random.randint(90, 140))
                print("CNPJ inserido.")

                await campo_cnpj_cpf.press("ArrowLeft")
                random_delay()

                await page.locator("#envia-identificador-otp").click()
                print("Primeiro botão 'Entrar' clicado.")
                random_delay()

                campo_senha = await page.wait_for_selector("#senha-identificador", timeout=10000)
                await campo_senha.fill(senha)
                print("Senha inserida.")
                random_delay()

                await page.locator("#envia-identificador").click()
                print("Segundo botão 'Entrar' clicado.")
                await asyncio.sleep(15)

                if await page.locator("//span[contains(text(), 'Atenção')]").is_visible(timeout=3000):
                    print("Erro detectado, recarregando...")
                    await page.reload()
                    await asyncio.sleep(5)
                    continue

                if "/sua-conta/" in page.url:
                    print("Login bem sucedido!")
                    login_sucesso = True
                    break
                else:
                    print("Login falhou, tentando de novo...")
                    await page.reload()
                    await asyncio.sleep(5)

            if not login_sucesso:
                print("Não conseguiu logar após várias tentativas.")
                return None

            cookies = await context.cookies()
            local_storage = await page.evaluate("JSON.stringify(localStorage);")
            session_storage = await page.evaluate("JSON.stringify(sessionStorage);")

            cnpj = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json"), "w") as file:
                json.dump(cookies, file)
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json"), "w") as file:
                file.write(local_storage)
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json"), "w") as file:
                file.write(session_storage)

            print("Cookies e storages salvos.")
            return {
                "cookies": cookies,
                "localStorage": json.loads(local_storage),
                "sessionStorage": json.loads(session_storage)
            }

        except Exception as e:
            print(f"Erro: {e}")
            return None

        finally:
            await browser.close()
            print("Navegador fechado.")
