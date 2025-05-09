from flask import Flask, request, jsonify, redirect
import requests
import os
import base64
import uuid
from difflib import SequenceMatcher

app = Flask(__name__)

# Bling
CLIENT_ID = os.getenv('BLING_CLIENT_ID')
CLIENT_SECRET = os.getenv('BLING_CLIENT_SECRET')
REDIRECT_URI = 'https://assistente-bling.onrender.com/callback'
TOKEN_URL = 'https://www.bling.com.br/Api/v3/oauth/token'
AUTH_URL = 'https://www.bling.com.br/Api/v3/oauth/authorize'
TOKEN_FILE = 'token.txt'


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
