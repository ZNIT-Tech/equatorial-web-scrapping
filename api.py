import os
import zipfile
from flask import Flask, request, jsonify, send_file
from scrapper import scrape_data

DOWLOAD_DIR = os.getenv("DOWNLOAD_DIR", "download")
os.makedirs(DOWLOAD_DIR, exist_ok=True)

# Função para criar o arquivo ZIP
def criar_zip_com_pdfs(diretorio_download, arquivos_pdf):
    zip_path = os.path.join(diretorio_download, "faturas.zip")
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for arquivo in arquivos_pdf:
            caminho_pdf = os.path.join(diretorio_download, arquivo)
            zipf.write(caminho_pdf, os.path.basename(caminho_pdf))  # Adiciona o arquivo ao ZIP
    
    return zip_path

# Função para fazer o scraping e retornar os PDFs
def scrape_data_with_zip(client_cpf_cnpj: str, senha: str, estado: str):
    # Chama a função scrape_data para baixar os PDFs
    scrape_data(client_cpf_cnpj, senha, estado)
    
    # Após o scraping, cria o arquivo ZIP com os PDFs baixados
    arquivos_pdf = [arquivo for arquivo in os.listdir(DOWLOAD_DIR) if arquivo.endswith(".pdf")]
    
    if arquivos_pdf:
        caminho_zip = criar_zip_com_pdfs(DOWLOAD_DIR, arquivos_pdf)
        return caminho_zip
    else:
        return None

# API Flask
app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json
    client_cpf_cnpj = data.get("client_cpf_cnpj")
    senha = data.get("senha")
    estado = data.get("estado")

    if not client_cpf_cnpj or not senha or not estado:
        return jsonify({"error": "Campos obrigatórios: cpf_cnpj, senha e estado"}), 400

    # Chama a função de scraping e cria o ZIP
    zip_path = scrape_data_with_zip(client_cpf_cnpj, senha, estado)

    if not zip_path:
        return jsonify({"error": "Nenhum PDF encontrado"}), 500

    return send_file(zip_path, as_attachment=True, download_name="faturas.zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
