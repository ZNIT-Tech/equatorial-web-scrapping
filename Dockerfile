# Usa uma imagem do Selenium com Chrome embutido
FROM selenium/standalone-chrome:latest

# Instala dependências necessárias para Python e WebDriver
USER root
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o contêiner
COPY requirements.txt .
COPY scrapper.py .  

# Cria um ambiente virtual
RUN python3 -m venv /venv

# Ativa o ambiente virtual
ENV PATH="/venv/bin:$PATH"

# Instala bibliotecas Python necessárias
RUN /venv/bin/pip install -r requirements.txt

# Configura variáveis para o Selenium
ENV DISPLAY=:99

# Comando para rodar o script automaticamente
CMD ["python3", "/app/scrapper.py"]  