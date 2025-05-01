

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai

load_dotenv()

app = Flask(__name__)

openai.api_key = os.getenv(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)
bling_api_key = os.getenv(bfa28c2bba8418312ea5a826c48cb4e3e03f8bbbdec46fec8d8c60a15d4386dfe5c4ec2f)

@app.route("/perguntar", methods=["POST"])
def perguntar():
    data = request.get_json()
    pergunta = data.get("pergunta", "")

    nome_produto = extrair_nome_produto(pergunta)  # Aqui está simplificado
    info_produto = buscar_no_bling(nome_produto)
    resposta = gerar_resposta_openai(pergunta, info_produto)

    return jsonify({"resposta": resposta})

def buscar_no_bling(nome_produto):
    url = f"https://bling.com.br/Api/v2/produtos/json/?apikey={bling_api_key}&descricao={nome_produto}"
    response = requests.get(url)
    produtos = response.json().get("retorno", {}).get("produtos", [])
    if produtos:
        produto = produtos[0]["produto"]
        return f"O produto '{produto['descricao']}' custa R$ {produto['preco']}."
    return "Não encontrei esse produto no sistema."

def gerar_resposta_openai(pergunta_cliente, dados_do_bling):
    prompt = f"O cliente perguntou: '{pergunta_cliente}'. Use estas informações para responder: {dados_do_bling}"
    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Você é um atendente virtual de uma empresa."},
            {"role": "user", "content": prompt}
        ]
    )
    return resposta["choices"][0]["message"]["content"]

def extrair_nome_produto(pergunta):
    # Você pode aprimorar isso com regex ou até NLP se quiser mais precisão
    return pergunta.strip()

if __name__ == "__main__":
    app.run(debug=True)