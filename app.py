from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import uuid
from difflib import SequenceMatcher
from openai import OpenAI

app = Flask(__name__)

# Bling
CLIENT_ID = os.getenv('BLING_CLIENT_ID')
CLIENT_SECRET = os.getenv('BLING_CLIENT_SECRET')
REDIRECT_URI = 'https://assistente-bling.onrender.com/callback'
TOKEN_URL = 'https://www.bling.com.br/Api/v3/oauth/token'
AUTH_URL = 'https://www.bling.com.br/Api/v3/oauth/authorize'
TOKEN_FILE = 'token.txt'

# OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def home():
    return 'API da Assistente está online!'

@app.route('/login')
def login():
    state = str(uuid.uuid4())
    auth_link = (
        f'{AUTH_URL}?response_type=code'
        f'&client_id={CLIENT_ID}'
        f'&redirect_uri={REDIRECT_URI}'
        f'&state={state}'
    )
    return redirect(auth_link)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return 'Código de autorização não encontrado', 400

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }

    auth_string = f'{CLIENT_ID}:{CLIENT_SECRET}'
    auth_base64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {auth_base64}'
    }

    response = requests.post(TOKEN_URL, data=data, headers=headers)

    if response.status_code != 200:
        return f'Erro ao obter token: {response.status_code} - {response.text}', 400

    tokens = response.json()
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')

    if access_token:
        with open(TOKEN_FILE, 'w') as f:
            f.write(access_token)
        return 'Autenticação concluída com sucesso! Token obtido.'
    else:
        return 'Erro: access_token não retornado pelo Bling.', 400

def carregar_token():
    try:
        with open(TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def buscar_produto_bling(nome_produto):
    access_token = carregar_token()
    if not access_token:
        return 'Erro: Token não encontrado. Faça login em /login'

    url = 'https://www.bling.com.br/Api/v3/produtos'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'descricao': nome_produto}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f'Erro ao buscar produtos: {response.status_code} - {response.text}'

        data = response.json()
        produtos = data.get('data', [])

        if not produtos:
            return 'Nenhum produto encontrado com esse nome.'

        resposta_formatada = []

        for item in produtos:
            nome_item = item.get('nome', '')
            similaridade = SequenceMatcher(None, nome_produto.lower(), nome_item.lower()).ratio()
            if similaridade < 0.4:
                continue

            descricao = nome_item
            preco_info = item.get('preco', {})
            preco = preco_info.get('preco', '0.00') if isinstance(preco_info, dict) else preco_info

            resposta_formatada.append(f'{descricao}')

            variacoes = item.get('variacoes', [])
            if variacoes:
                for v in variacoes:
                    nome_var = v.get('nome', 'Variação')
                    preco_info_var = v.get('preco', {})
                    preco_var = preco_info_var.get('preco', preco) if isinstance(preco_info_var, dict) else preco_info_var
                    resposta_formatada.append(f'- {nome_var} | R$ {preco_var}')
            else:
                resposta_formatada.append(f'- Preço: R$ {preco}')

        if not resposta_formatada:
            return 'Nenhum produto semelhante encontrado com esse nome.'

        return '\n'.join(resposta_formatada)

    except Exception as e:
        return f'Erro ao interpretar resposta do Bling: {str(e)}'

@app.route('/buscar_produto_bling', methods=['POST'])
def buscar_produto_openai():
    try:
        data = request.get_json()
        nome_produto = data.get('nome_produto')
        if not nome_produto:
            return jsonify({'erro': 'Nome do produto não informado.'}), 400

        resultado = buscar_produto_bling(nome_produto)
        return jsonify({'resultado': resultado})

    except Exception as e:
        return jsonify({'erro': f'Erro ao buscar produto: {str(e)}'}), 500

if __name__ == '__main__':
    import sys
    if 'RENDER' in os.environ:
        from waitress import serve
        serve(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        app.run(debug=True)
