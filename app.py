from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import logging

# Configura o logging para mostrar mensagens de depuração
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Configurações do aplicativo (use variáveis de ambiente seguras no Render)
CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
REDIRECT_URI = "https://assistente-bling.onrender.com/callback"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"

# Armazenar o access_token temporariamente
ACCESS_TOKEN = None

@app.route("/")
def home():
    return "API da Assistente está online!"

@app.route("/login")
def login():
    auth_link = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    logging.debug(f"Redirecionando para URL de autenticação: {auth_link}")
    return redirect(auth_link)

@app.route("/callback")
def callback():
    # Recebe o código de autorização enviado pelo Bling após o login
    code = request.args.get("code")
    if not code:
        logging.error("Código de autorização não encontrado")
        return "Código de autorização não encontrado", 400

    # Dados para enviar na requisição de token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    # Gera o cabeçalho de autenticação com client_id e client_secret
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_base64}"
    }

    logging.debug(f"Enviando requisição para obter token com dados: {data}")

    response = requests.post(TOKEN_URL, data=data, headers=headers)

    if response.status_code != 200:
        logging.error(f"Erro ao obter token: {response.status_code} - {response.text}")
        return f"Erro ao obter token: {response.status_code} - {response.text}", 400

    global ACCESS_TOKEN
    ACCESS_TOKEN = response.json().get("access_token")

    if ACCESS_TOKEN:
        logging.debug(f"Token de acesso obtido: {ACCESS_TOKEN}")
        return f"Autenticação concluída com sucesso! Token obtido."
    else:
        logging.error("Erro: access_token não retornado pelo Bling.")
        return "Erro: access_token não retornado pelo Bling.", 400

def buscar_produto_bling(nome_produto):
    if not ACCESS_TOKEN:
        logging.error("Erro: Token de acesso não encontrado. Faça login em /login")
        return "Erro: Token de acesso não encontrado. Faça login em /login"

    url = "https://www.bling.com.br/Api/v3/produtos"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {"descricao": nome_produto}

    logging.debug(f"Realizando requisição para buscar o produto: {nome_produto}")

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        logging.error(f"Erro na requisição de produto: {response.status_code} - {response.text}")
        return f"Erro: {response.status_code} - {response.text}"

    try:
        produtos = response.json()['data']
    except KeyError:
        logging.error("Produto não encontrado no Bling.")
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
