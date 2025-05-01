
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

def buscar_produto_bling(nome_produto):
    api_key = os.getenv("BLING_API_KEY")
    if not api_key:
        return "Erro: Chave da API (BLING_API_KEY) nao encontrada."

    url = "https://api.bling.com.br/produtos"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    params = {
        "descricao": nome_produto
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return f"Erro: {response.status_code} - {response.text}"

    try:
        produtos = response.json().get('data', [])
    except (KeyError, ValueError):
        return "Erro ao interpretar resposta da API."

    if not produtos:
        return "Produto nao encontrado no Bling."

    resposta_formatada = []

    for produto in produtos:
        descricao = produto.get('descricao', 'Sem descricao')
        preco = produto.get('preco', '0.00')
        variacoes = produto.get('variacoes', [])

        resposta_formatada.append(f"{descricao}")

        if variacoes:
            for v in variacoes:
                nome_var = v.get('nome', 'Variação')
                preco_var = v.get('preco', preco)
                resposta_formatada.append(f"- {nome_var} | R$ {preco_var}")
        else:
            resposta_formatada.append(f"- Preco: R$ {preco}")

    return "\n".join(resposta_formatada)

@app.route("/produto", methods=["POST"])
def produto():
    data = request.get_json()
    nome = data.get("nome")

    if not nome:
        return jsonify({"erro": "Informe o nome do produto"}), 400

    resultado = buscar_produto_bling(nome)
    return jsonify({"resultado": resultado})

@app.route("/")
def home():
    return "API da Assistente está online!"

if __name__ == "__main__":
    app.run(debug=True)
