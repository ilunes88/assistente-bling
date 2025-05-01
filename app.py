
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

def buscar_produto_bling(nome_produto):
    api_key = os.getenv("BLING_API_KEY")
    url = "https://bling.com.br/Api/v3/produtos/json/"
    params = {
        "apikey": api_key,
        "descricao": nome_produto
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return f"Erro: {response.status_code} - {response.text}"

    try:
        produtos = response.json()['retorno']['produtos']
    except KeyError:
        return "Produto não encontrado no Bling."

    resposta_formatada = []

    for item in produtos:
        produto = item['produto']
        descricao = produto.get('descricao', 'Sem descrição')
        preco = produto.get('preco', '0.00')
        variacoes = produto.get('variacoes', [])

        # Adiciona o título principal
        resposta_formatada.append(f"{descricao}")

        # Se houver variações, exibe cada uma
        if variacoes:
            for v in variacoes:
                nome_var = v.get('nome', 'Variação')
                preco_var = v.get('preco', preco)
                resposta_formatada.append(f"- {nome_var} | R$ {preco_var}")
        else:
            # Sem variação, mostra o preço principal
            resposta_formatada.append(f"- Preço: R$ {preco}")

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

if __name__ == "__main__":
    app.run(debug=True)
