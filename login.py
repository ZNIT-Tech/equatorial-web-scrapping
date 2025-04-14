import asyncio
import json
import os
import random
import time
from playwright.async_api import async_playwright
from urllib.parse import urlparse

# Configurações
COOKIES_DIR = "cookies"
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)

# Lista de user agents realistas
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

def random_delay(min_delay=1, max_delay=5):
    time.sleep(random.uniform(min_delay, max_delay))

async def human_type(element, text, min_delay=0.05, max_delay=0.3):
    for char in text:
        await element.type(char, delay=random.uniform(min_delay, max_delay))
        if random.random() > 0.9:  # 10% chance de pequena pausa
            await asyncio.sleep(random.uniform(0.2, 0.5))

async def save_Credentials(client_cpf_cnpj: str, senha: str, estado: str):
    # Configuração mais realista do navegador
    user_agent = random.choice(USER_AGENTS)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Tente com headless=False primeiro para debug
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-extensions',
                '--disable-popup-blocking'
            ]
        )
        
        context = await browser.new_context(
            user_agent=user_agent,
            accept_downloads=True,
            viewport={'width': 1366, 'height': 768},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            permissions=['geolocation'],
            color_scheme='light'
        )
        
        # Remover propriedades que identificam automação
        await context.add_init_script("""
            delete navigator.__proto__.webdriver;
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            window.chrome = { runtime: {}, };
        """)
        
        page = await context.new_page()
        
        try:
            # Navegação mais humana
            await page.goto("https://pi.equatorialenergia.com.br/", wait_until="networkidle")
            print("Página carregada.")
            
            # Movimento de mouse aleatório antes de interagir
            await page.mouse.move(random.randint(0, 500), random.randint(0, 500))
            
            # Aceitar cookies (se existir)
            try:
                await page.locator("#onetrust-accept-btn-handler").click(timeout=3000)
                print("Cookies aceitos.")
                random_delay(1, 2)
            except:
                print("Nenhum botão de cookies encontrado.")
            
            # Continuar no site (se existir)
            try:
                await page.locator("//button[contains(text(), 'Continuar no site')]").click(timeout=3000)
                print("Continuando no site.")
                random_delay(1, 3)
            except:
                print("Nenhum botão 'Continuar no site' encontrado.")
            
            # Aceitar termos (se existir)
            try:
                await page.locator("#aviso_aceite").click(timeout=3000)
                print("Aviso de aceite marcado.")
                random_delay(0.5, 1.5)
            except:
                print("Nenhum checkbox de aviso encontrado.")
            
            # LGPD (se existir)
            try:
                await page.locator("#lgpd_accept").click(timeout=3000)
                print("Enviado aceite LGPD.")
                random_delay(0.5, 1.5)
            except:
                print("Nenhum checkbox LGPD encontrado.")
            
            login_sucesso = False
            tentativas = 0
            max_tentativas = 5
            
            while not login_sucesso and tentativas < max_tentativas:
                tentativas += 1
                print(f"Tentativa de login #{tentativas}...")
                
                try:
                    # Preencher CPF/CNPJ de forma mais humana
                    campo_cnpj_cpf = await page.wait_for_selector("#identificador-otp", timeout=10000)
                    await campo_cnpj_cpf.click()
                    random_delay(0.2, 0.5)
                    
                    cnpj_cpf_limpo = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
                    await human_type(campo_cnpj_cpf, cnpj_cpf_limpo)
                    
                    # Pressionar Tab em vez de ArrowLeft para parecer mais humano
                    await campo_cnpj_cpf.press("Tab")
                    random_delay(0.5, 1.5)
                    
                    # Clicar no botão de forma mais humana
                    btn_entrar = await page.wait_for_selector("#envia-identificador-otp", timeout=5000)
                    await btn_entrar.hover()
                    random_delay(0.3, 0.8)
                    await btn_entrar.click()
                    
                    # Esperar pela transição
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    random_delay(1, 3)
                    
                    # Preencher senha
                    campo_senha = await page.wait_for_selector("#senha-identificador", timeout=10000)
                    await campo_senha.click()
                    random_delay(0.2, 0.5)
                    await human_type(campo_senha, senha)
                    
                    # Clicar no botão de login
                    btn_login = await page.wait_for_selector("#envia-identificador", timeout=5000)
                    await btn_login.hover()
                    random_delay(0.5, 1.5)
                    await btn_login.click()
                    
                    # Esperar por redirecionamento ou erro
                    try:
                        await page.wait_for_url("**/sua-conta/**", timeout=20000)
                        login_sucesso = True
                        print("Login bem sucedido!")
                        break
                    except:
                        # Verificar se há mensagem de erro
                        try:
                            erro = await page.wait_for_selector("//span[contains(text(), 'Atenção')]", timeout=3000)
                            if erro:
                                print(f"Erro de login detectado: {await erro.inner_text()}")
                                await page.reload()
                                await asyncio.sleep(5)
                                continue
                        except:
                            pass
                        
                        print("Tempo de espera excedido, tentando novamente...")
                        await page.reload()
                        await asyncio.sleep(5)
                
                except Exception as e:
                    print(f"Erro durante tentativa de login: {str(e)}")
                    await page.reload()
                    await asyncio.sleep(5)
            
            if not login_sucesso:
                print("Falha no login após várias tentativas. Verifique as credenciais.")
                return None
            
            # Salvar estado da sessão
            cnpj = client_cpf_cnpj.replace(".", "").replace("/", "").replace("-", "")
            
            # Cookies
            cookies = await context.cookies()
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_cookies.json"), "w") as file:
                json.dump(cookies, file)
            
            # Local Storage
            local_storage = await page.evaluate("() => JSON.stringify(window.localStorage);")
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_localStorage.json"), "w") as file:
                file.write(local_storage)
            
            # Session Storage
            session_storage = await page.evaluate("() => JSON.stringify(window.sessionStorage);")
            with open(os.path.join(COOKIES_DIR, f"{cnpj}_sessionStorage.json"), "w") as file:
                file.write(session_storage)
            
            print("Cookies e storage salvos com sucesso.")
            
            return {
                "cookies": cookies,
                "localStorage": json.loads(local_storage),
                "sessionStorage": json.loads(session_storage)
            }
        
        except Exception as e:
            print(f"Erro geral: {str(e)}")
            return None
        
        finally:
            await browser.close()
            print("Navegador fechado.")