from flask import Flask, request, jsonify, redirect
import requests
import os

app = Flask(__name__)

# Configurações do aplicativo (substitua com seus dados)
CLIENT_ID = os.getenv("BLING_CLIENT_ID")
CLIENT_SECRET = os.getenv("BLING_CLIENT_SECRET")
REDIRECT_URI = "https://assistente-bling.onrender.com/callback"
TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
AUTH_URL = "https://www.bling.com.br/Api/v3/oauth/authorize"

# Armazenar o access_token temporariamente (ideal usar um banco de dados seguro)
ACCESS_TOKEN = None

@app.route("/")
def home():
    return "API da Assistente está online!"

@app.route("/login")
def login():
    # URL para autenticação no Bling, onde o usuário irá conceder permissões
    auth_link = f"{AUTH_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return redirect(auth_link)

@app.route("/callback")
def callback():
    # Recebe o código de autorização enviado pelo Bling após o login
    code = request.args.get("code")
    if not code:
        return "Código de autorização não encontrado", 400

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=data, headers=headers)

    if response.status_code != 200:
        return f"Erro ao obter token: {response.status_code} - {response.text}", 400

    global ACCESS_TOKEN
    ACCESS_TOKEN = response.json().get("access_token")
    return "Autenticação concluída com sucesso!"

def buscar_produto_bling(nome_produto):
    # Verificar se o token de acesso está presente
    if not ACCESS_TOKEN:
        return "Erro: Token de acesso não encontrado. Faça login em /login"

    # Realiza a requisição para a API do Bling com o token de acesso
    url = f"https://www.bling.com.br/Api/v3/produtos/json/"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {"descricao": nome_produto}

    response = requests.get(url, headers=headers, params=params)

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

if __name__ == "__main__":
    app.run(debug=True)
