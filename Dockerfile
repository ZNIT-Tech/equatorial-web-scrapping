# Usa uma imagem base do Python
FROM python:3.11

# Instala dependências do sistema para o Chrome e WebDriver
RUN apt-get update && apt-get install -y \
    unzip \
    wget \
    curl \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libappindicator3-1 \
    fonts-liberation \
    libasound2 \
    libgbm1 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instala o Chrome
RUN wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > /tmp/chrome.deb \
    && dpkg -i /tmp/chrome.deb || apt-get -fy install \
    && rm /tmp/chrome.deb

# Instala o ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

RUN apt-get update && apt-get install -y wget curl unzip \
&& wget -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
&& apt-get install -y /tmp/chrome.deb \
&& rm /tmp/chrome.deb


# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposição da porta do Flask
EXPOSE 5000

# Comando para rodar a aplicação Flask
CMD ["python", "api.py"]
