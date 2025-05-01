from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

def buscar_produto_bling(nome_produto):
    token = os.getenv("BLING_API_KEY")
    url = f"https://api.bling.com.br/produtos?descricao={nome_produto}"

    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"Erro: {response.status_code} - {response.text}"

    try:
        dados = response.json()
        produtos = dados.get("data", [])
    except Exception as e:
        return f"Erro ao processar resposta: {str(e)}"

    if not produtos:
        return "Produto não encontrado no Bling."

    resposta_formatada = []

    for produto in produtos:
        nome = produto.get("nome", "Sem nome")
        preco = produto.get("preco", {}).get("preco", "0.00")

        resposta_formatada.append(f"{nome} - Preço: R$ {preco}")

        variacoes = produto.get("variacoes", [])
        for var in variacoes:
            nome_var = var.get("nome", "Variação")
            preco_var = var.get("preco", {}).get("preco", preco)
            resposta_formatada.append(f"- {nome_var} | R$ {preco_var}")

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
    app.run()
