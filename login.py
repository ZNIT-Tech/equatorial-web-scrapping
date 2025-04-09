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

def random_delay(min_delay=1, max_delay=3):
    time.sleep(random.uniform(min_delay, max_delay))

async def save_Credentials(client_cpf_cnpj: str, senha: str, estado: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # mantém headless pra servidor
            slow_mo=50      # deixa as ações mais humanas
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            accept_downloads=True
        )

        # Página
        page = await context.new_page()

        # Remover detecção de webdriver e adicionar mocks humanos
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt'] });
            Object.defineProperty(navigator, 'platform', { get: () => 'Linux x86_64' });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        # Debug do console da página
        page.on("console", lambda msg: print(f"[console] {msg.type}: {msg.text}"))

        try:
            await page.goto("https://pi.equatorialenergia.com.br/")
            print("Página carregada.")

            try:
                await page.locator("#onetrust-accept-btn-handler").click(timeout=5000)
                print("Cookies aceitos.")
            except:
                print("Nenhum botão de cookies encontrado.")

            random_delay()
            await page.locator("//button[contains(text(), 'Continuar no site')]").click()
            await page.locator("#aviso_aceite").click()
            await page.locator("#lgpd_accept").click()
            print("Aceites e avisos confirmados.")

            login_sucesso = False
            tentativas = 0

            while not login_sucesso and tentativas < 5:
                tentativas += 1
                print(f"Tentativa de login #{tentativas}...")

                campo_cnpj_cpf = await page.wait_for_selector("#identificador-otp")
                cnpj_cpf_limpo = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
                for char in cnpj_cpf_limpo:
                    await campo_cnpj_cpf.type(char, delay=100)

                await campo_cnpj_cpf.press("ArrowLeft")
                await page.locator("#envia-identificador-otp").click()
                random_delay()

                campo_senha = await page.wait_for_selector("#senha-identificador")
                await campo_senha.fill(senha)
                await page.locator("#envia-identificador").click()
                print("Tentando login...")

                await asyncio.sleep(15)

                if await page.locator("//span[contains(text(), 'Atenção')]").is_visible():
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

            print("Cookies e storage salvos com sucesso.")

            return {
                "cookies": cookies,
                "localStorage": json.loads(local_storage),
                "sessionStorage": json.loads(session_storage)
            }

        except Exception as e:
            print(f"Erro geral: {e}")
            return None

        finally:
            await browser.close()
            print("Navegador fechado.")
