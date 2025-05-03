from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import uuid
from difflib import SequenceMatcher

app = Flask(__name__)

CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
REDIRECT_URI = "https://assistente-bling.onrender.com/callback"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
TOKEN_FILE = "token.txt"

@app.route("/")
def home():
    return "API da Assistente está online!"

@app.route("/login")
def login():
    state = str(uuid.uuid4())
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

    access_token = response.json().get("access_token")

    if access_token:
        with open(TOKEN_FILE, "w") as f:
            f.write(access_token)
        return "Autenticação concluída com sucesso! Token obtido."
    else:
        return "Erro: access_token não retornado pelo Bling.", 400

def carregar_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def buscar_produto_bling(nome_produto):
    access_token = carregar_token()
    if not access_token:
        return "Erro: Token não encontrado. Faça login em /login"

    url = "https://www.bling.com.br/Api/v3/produtos"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 100}  # Pega até 100 produtos

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Erro ao buscar produtos: {response.status_code} - {response.text}"

        data = response.json()
        produtos = data.get('data', [])
        resultados = []

        for item in produtos:
            nome_principal = item.get('nome', '').lower()
            encontrou = False

            if nome_produto.lower() in nome_principal:
                encontrou = True
                descricao = item.get('nome', 'Sem descrição')
                preco_info = item.get('preco', {})
                preco = preco_info.get('preco', '0.00') if isinstance(preco_info, dict) else preco_info
                resultados.append(f"{descricao}\n- Preço: R$ {preco}")

            variacoes = item.get('variacoes', [])
            for v in variacoes:
                nome_var = v.get('nome', '').lower()
                if nome_produto.lower() in nome_var:
                    encontrou = True
                    preco_info_var = v.get('preco', {})
                    preco_var = preco_info_var.get('preco', '0.00') if isinstance(preco_info_var, dict) else preco_info_var
                    resultados.append(f"{v.get('nome', 'Variação')}\n- Preço: R$ {preco_var}")

        if not resultados:
            return "Nenhum produto ou variação encontrada com esse nome."

        return "\n".join(resultados)

    except Exception as e:
        return f"Erro ao interpretar resposta: {str(e)}"

@app.route("/produto", methods=["POST"])
def produto():
    try:
        data = request.get_json()
        nome = data.get("nome")

        if not nome:
            return jsonify({"erro": "Informe o nome do produto"}), 400

        resultado = buscar_produto_bling(nome)
        return jsonify({"resultado": resultado})

    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 500

@app.route("/verifica_token")
def verifica_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if token:
                return jsonify({"status": "Token carregado com sucesso", "token": token})
            else:
                return jsonify({"status": "Token vazio"})
    except FileNotFoundError:
        return jsonify({"status": "Arquivo token.txt não encontrado"})

if __name__ == "__main__":
    app.run(debug=True)
