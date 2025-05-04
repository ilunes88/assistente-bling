from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import uuid
from difflib import SequenceMatcher
import openai  # Importando OpenAI para integração futura

app = Flask(__name__)

CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
REDIRECT_URI = "https://assistente-bling.onrender.com/callback"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
TOKEN_FILE = "token.txt"

# Configuração da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    params = {"descricao": nome_produto}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Erro ao buscar produtos: {response.status_code} - {response.text}"

        data = response.json()
        produtos = data.get('data', [])

        if not produtos:
            return "Nenhum produto encontrado com esse nome."

        resposta_formatada = []

        for item in produtos:
            nome_item = item.get('nome', '')
            similaridade = SequenceMatcher(None, nome_produto.lower(), nome_item.lower()).ratio()
            if similaridade < 0.6:
                continue

            descricao = nome_item
            preco_info = item.get('preco', {})
            preco = preco_info.get('preco', '0.00') if isinstance(preco_info, dict) else preco_info

            resposta_formatada.append(f"{descricao}")

            # Verifica variações do produto
            variacoes = item.get('variacoes', [])
            if variacoes:
                for v in variacoes:
                    nome_var = v.get('nome', 'Variação')
                    preco_info_var = v.get('preco', {})
                    preco_var = preco_info_var.get('preco', preco) if isinstance(preco_info_var, dict) else preco_info_var
                    resposta_formatada.append(f"- {nome_var} | R$ {preco_var}")
            else:
                resposta_formatada.append(f"- Preço: R$ {preco}")

        if not resposta_formatada:
            return "Nenhum produto semelhante encontrado com esse nome."

        return "\n".join(resposta_formatada)

    except Exception as e:
        return f"Erro ao interpretar resposta: {str(e)}"

def chamar_openai(query):
    try:
        # Fazendo uma chamada à API da OpenAI para processar a consulta
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Usando modelo GPT-3.5, altere conforme necessário
            messages=[  # Estrutura de mensagens com 'role' e 'content'
                {"role": "system", "content": "Você é um assistente de atendimento ao cliente."},
                {"role": "user", "content": query}
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Erro ao processar a consulta com OpenAI: {str(e)}"

@app.route("/produto", methods=["POST"])
def produto():
    try:
        data = request.get_json()
        nome = data.get("nome")

        if not nome:
            return jsonify({"erro": "Informe o nome do produto"}), 400

        resultado_bling = buscar_produto_bling(nome)
        
        # Se o produto for encontrado, processa a resposta com a OpenAI
        if "Nenhum produto encontrado" not in resultado_bling:
            resultado_openai = chamar_openai(f"Qual a descrição do produto {nome}?")
            return jsonify({"resultado": resultado_bling, "descricao_openai": resultado_openai})

        return jsonify({"resultado": resultado_bling})

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
