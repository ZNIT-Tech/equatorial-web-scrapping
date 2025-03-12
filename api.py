import os
from flask import Flask, request, jsonify, send_file
from scrapper import scrape_data

app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json
    client_cpf_cnpj = data.get("client_cpf_cnpj")
    senha = data.get("senha")
    estado = data.get("estado")

    if not client_cpf_cnpj or not senha or not estado:
        return jsonify({"error": "Campos obrigatórios: cpf_cnpj, senha e estado"}), 400

    pdf_path = scrape_data(client_cpf_cnpj, senha, estado)

    if not pdf_path:
        return jsonify({"error": "Nenhum PDF encontrado"}), 500

    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
