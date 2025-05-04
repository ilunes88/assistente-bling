from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import uuid
from difflib import SequenceMatcher
import openai

app = Flask(__name__)

# Bling
CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
REDIRECT_URI = "https://assistente-bling.onrender.com/callback"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"
TOKEN_FILE = "token.txt"

# OpenAI
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
        return f"Erro ao interpretar resposta do Bling: {str(e)}"

def chamar_openai(contexto_produto):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente de atendimento ao cliente. Gere uma descrição útil e clara do produto com base nas informações fornecidas."},
                {"role": "user", "content": f"Descreva este produto com base nos dados: {contexto_produto}"}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERRO OPENAI] {str(e)}")
        return "Erro ao processar a descrição com OpenAI: " + str(e)

@app.route("/produto", methods=["POST"])
def produto():
    try:
        data = request.get_json()
        nome = data.get("nome")

        if not nome:
            return jsonify({"erro": "Informe o nome do produto"}), 400

        resultado_bling = buscar_produto_bling(nome)

        if "Nenhum produto encontrado" not in resultado_bling and "Erro" not in resultado_bling:
            resultado_openai = chamar_openai(resultado_bling)
            return jsonify({
                "resultado": resultado_bling,
                "descricao_openai": resultado_openai
            })

        return jsonify({
            "resultado": resultado_bling,
            "descricao_openai": "Produto não localizado para descrição."
        })

    except Exception as e:
        return jsonify({"erro": f"Erro inesperado: {str(e)}"}), 500

@app.route("/verifica_token")
def verifica_token():
    token = carregar_token()
    if token:
        return jsonify({"status": "Token carregado com sucesso", "token": token})
    else:
        return jsonify({"status": "Token não encontrado"})

# Novo endpoint de verificação de ambiente e conexão com OpenAI
@app.route("/verifica_ambiente")
def verifica_ambiente():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"erro": "OPENAI_API_KEY não está definida."}), 500

    try:
        # Tenta chamada simples à OpenAI
        resposta = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Teste de conexão"}
            ],
            max_tokens=5
        )
        return jsonify({
            "status": "OK",
            "resposta": resposta.choices[0].message.content.strip()
        })
    except Exception as e:
        return jsonify({"erro": f"Erro ao conectar à OpenAI: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
