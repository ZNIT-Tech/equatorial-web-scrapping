FROM python:3.11

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV DOWNLOAD_DIR=/app/download

# Instala dependências
RUN apt-get update && apt-get install -y \
    unzip wget curl xvfb libxi6 libgconf-2-4 libnss3 libxss1 \
    libappindicator3-1 fonts-liberation libasound2 libgbm1 \
    xdg-utils supervisor x11vnc xfce4 \
    && rm -rf /var/lib/apt/lists/*

# Instala o Chrome
RUN wget -qO- https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb > /tmp/chrome.deb \
    && dpkg -i /tmp/chrome.deb || apt-get -fy install \
    && rm /tmp/chrome.deb

# Instala ChromeDriver
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Copia os arquivos do projeto
WORKDIR /app
COPY . .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala Playwright e browsers
RUN playwright install

# Cria pastas necessárias
RUN mkdir -p /var/log/supervisor $DOWNLOAD_DIR /root/.vnc

# Define senha VNC como 'senha'
RUN x11vnc -storepasswd senha /root/.vnc/passwd

# Copia configuração do supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expõe a porta do VNC e da sua API Flask
EXPOSE 5900 5000

# Inicia todos os serviços (VNC + X11 + Flask)
CMD ["/usr/bin/supervisord"]
