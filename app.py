from flask import Flask, request, jsonify
import requests
import os
from openai import OpenAI

app = Flask(__name__)

# Configurações do Bling e OpenAI
CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
TOKEN_FILE = "token.txt"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def carregar_token():
    """ Carrega o token do Bling a partir de um arquivo local. """
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def buscar_produto_bling(nome_produto):
    """ Realiza a busca de um produto no Bling pelo nome. """
    access_token = carregar_token()
    if not access_token:
        return "Erro: Token não encontrado. Faça login no Bling."

    url = "https://www.bling.com.br/Api/v3/produtos"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"descricao": nome_produto}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        return f"Erro ao buscar produtos: {response.status_code} - {response.text}"

    data = response.json().get('data', [])
    if not data:
        return "Nenhum produto encontrado com esse nome."

    resposta_formatada = []
    for item in data:
        nome_item = item.get('nome', '')
        preco_info = item.get('preco', {})
        preco = preco_info.get('preco', '0.00')
        resposta_formatada.append(f"{nome_item} - Preço: R$ {preco}")
    
    return "\n".join(resposta_formatada)

def chamar_openai(nome_produto):
    """ Realiza a interação com a OpenAI para retornar a descrição do produto. """
    resultado_bling = buscar_produto_bling(nome_produto)
    if "Erro" in resultado_bling or "Nenhum produto" in resultado_bling:
        return resultado_bling

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Você é um assistente que ajuda os usuários a encontrarem produtos e preços."},
            {"role": "user", "content": f"Descreva o produto: {resultado_bling}"}
        ],
        max_tokens=200
    )

    return response.choices[0].message.content.strip()

@app.route("/produto", methods=["POST"])
def produto():
    data = request.get_json()
    nome = data.get("nome")

    if not nome:
        return jsonify({"erro": "Informe o nome do produto"}), 400

    descricao = chamar_openai(nome)
    return jsonify({"descricao": descricao})

if __name__ == "__main__":
    app.run(debug=True)
