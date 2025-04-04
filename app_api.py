import os 
import asyncio
from flask import Flask, request, jsonify, send_file
from web_scrapper import testar_sessao, zip_pdfs, limpar_diretorio
from web_scrapper_usina import testar_sessao_usina
from login import save_Credentials

# API Flask
app = Flask(__name__)

DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/app/download')

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json
    cnpj_cpf = data.get("cnpj_cpf")

    cnpj_cpf = cnpj_cpf.replace(".", "").replace("/", "").replace("-", "")

    limpar_diretorio(DOWNLOAD_DIR)

    if not cnpj_cpf:
        return jsonify({"erro": "campo obrigatório cnpj_cpf não inserido"}), 400
    
    if not testar_sessao(cnpj_cpf):
        return jsonify({"erro": "Falha ao testar sessão"}), 500


    caminho_zip = zip_pdfs(DOWNLOAD_DIR)

    if caminho_zip:
        return send_file(caminho_zip, as_attachment=True, mimetype="application/zip")
    else:
        return jsonify({"erro": "Nenhum PDF encontrado para compactar"}), 404


@app.route("/scraper_usina", methods=["POST"])
def scrape_usina():
    data = request.json
    cnpj_cpf = data.get("cnpj_cpf")

    cnpj_cpf = cnpj_cpf.replace(".", "").replace("/", "").replace("-", "")

    if not cnpj_cpf:
        return jsonify({"erro": "campo obrigatório cnpj_cpf não inserido"}), 400
    
    limpar_diretorio(DOWNLOAD_DIR)
    
    if not testar_sessao_usina(cnpj_cpf):
        return jsonify({"erro": "Falha ao testar sessão"}), 500
    
    caminho_zip = zip_pdfs(DOWNLOAD_DIR)

    if caminho_zip:
        return send_file(caminho_zip, as_attachment=True, mimetype="application/zip")
    else:
        return jsonify({"erro": "Nenhum PDF encontrado para compactar"}), 404

@app.route("/login", methods=["POST"])
def save_credentials():
    data = request.json
    cnpj_cpf = data.get("cnpj_cpf")
    senha = data.get("senha")
    estado = data.get("estado")

    cnpj_cpf = cnpj_cpf.replace(".", "").replace("/", "").replace("-", "")

    if not cnpj_cpf or not senha or not estado:
        return jsonify({"erro": "campo obrigatório cnpj_cpf ou senha não inserido"}), 400

    try:
        asyncio.run(save_Credentials(cnpj_cpf, senha, estado))
        return jsonify({"mensagem": "Scraping concluído com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": f"Erro ao salvar credenciais: {str(e)}"}), 500
    


@app.route("/check", methods=["GET"])
def check():
    return jsonify({"status": "OK"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)