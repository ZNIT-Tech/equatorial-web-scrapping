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
    email_data = data.get("email_data")
    estado = data.get("estado")
    ucs = data.get("ucs")
    tipo = data.get("tipo")
    distribuidora = data.get("distribuidora")

    # Validação básica
    if not cnpj_cpf or not email_data or not estado:
        return jsonify({"erro": "campo obrigatório cnpj_cpf ou senha não inserido"}), 400

    # Garantir que UCs sejam sempre uma lista
    if isinstance(ucs, str):
        ucs = [ucs]
    elif not isinstance(ucs, list):
        ucs = []

    try:
        resultado = asyncio.run(save_Credentials(cnpj_cpf, email_data, estado))

        if resultado is None or "erro" in resultado:
            return jsonify(resultado or {"erro": "Erro desconhecido durante scraping"}), 400

        return jsonify({
            "mensagem": "Scraping concluído com sucesso!",
            "dados_recebidos": {
                "cnpj_cpf": cnpj_cpf,
                "email_data": email_data,
                "estado": estado,
                "ucs": ucs,
                "tipo": tipo,
                "distribuidora": distribuidora
            },
            "cookies": resultado.get("cookies"),
            "localStorage": resultado.get("localStorage"),
            "sessionStorage": resultado.get("sessionStorage")
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao salvar credenciais: {str(e)}"}), 500

    


@app.route("/check", methods=["GET"])
def check():
    return jsonify({"status": "OK"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)