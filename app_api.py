import os 
from flask import Flask, request, jsonify, send_file
from web_scrapper import testar_sessao, zip_pdfs, limpar_diretorio

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

@app.route("/check", methods=["GET"])
def check():
    return jsonify({"status": "OK"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)