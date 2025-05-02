from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import uuid

app = Flask(__name__)

# Configurações (use variáveis de ambiente seguras no Render)
CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
REDIRECT_URI = "https://assistente-bling.onrender.com/callback"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"

# Token temporário (idealmente usar banco de dados)
ACCESS_TOKEN = None

@app.route("/")
def home():
    return "API da Assistente está online!"

@app.route("/login")
def login():
    state = str(uuid.uuid4())  # Valor aleatório para segurança
    auth_link = (
        f"{AUTH_URL}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
    )
    return redirect(auth_link)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Código de autorização não encontrado", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_base64}"
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)

    if response.status_code != 200:
        return f"Erro ao obter token: {response.status_code} - {response.text}", 400

    global ACCESS_TOKEN
    ACCESS_TOKEN = response.json().get("access_token")

    if ACCESS_TOKEN:
        return "Autenticação concluída com sucesso! Token obtido."
    else:
        return "Erro: access_token não retornado pelo Bling.", 400


def buscar_produto_bling(nome_produto):
    if not ACCESS_TOKEN:
        return "Erro: Token de acesso não encontrado. Faça login em /login"

    url = "https://www.bling.com.br/Api/v3/produtos"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {"nome": nome_produto}  # CORRIGIDO

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return f"Erro: {response.status_code} - {response.text}"

    try:
        produtos = response.json()['data']
        if not produtos:
            return "Nenhum produto encontrado com esse nome."
    except KeyError:
        return "Produto não encontrado no Bling."

    resposta_formatada = []

    for item in produtos:
        descricao = item.get('nome', 'Sem descrição')
        preco = item.get('preco', {}).get('preco', '0.00')
        variacoes = item.get('variacoes', [])

        resposta_formatada.append(f"{descricao}")

        if variacoes:
            for v in variacoes:
                nome_var = v.get('nome', 'Variação')
                preco_var = v.get('preco', {}).get('preco', preco)
                resposta_formatada.append(f"- {nome_var} | R$ {preco_var}")
        else:
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

if __name__ == "__main__":
    app.run(debug=True)
