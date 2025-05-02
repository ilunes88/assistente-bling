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
