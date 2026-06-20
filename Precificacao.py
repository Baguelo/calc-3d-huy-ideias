from flask import Flask, jsonify, render_template, request
import os


app = Flask(__name__)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "CONFIGURACOES.txt")


def load_config():
    config = {}
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if "=" not in linha:
                raise ValueError(f"Linha {numero} inválida em CONFIGURACOES.txt")

            nome, valor_texto = linha.split("=", 1)
            nome = nome.strip().upper()
            valor_texto = valor_texto.split("#", 1)[0].strip().replace(",", ".")
            try:
                config[nome] = float(valor_texto)
            except ValueError as erro:
                raise ValueError(
                    f"Valor inválido para {nome} na linha {numero}"
                ) from erro
    return config


def valor(config, nome, padrao=0):
    return config.get(nome, padrao)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/calcular", methods=["POST"])
def calcular():
    dados = request.get_json(silent=True) or {}
    config = load_config()

    quantidade = max(1, int(dados.get("quantidade", 1)))
    peso = float(dados.get("peso", 0))
    tempo = float(dados.get("tempo", 0))
    filamento_kg = float(dados.get("filamento_kg", 0))
    embalagem = float(dados.get("embalagem", 0))
    mdo_horas = float(dados.get("mdo_horas", 0))
    mdo_valor = float(dados.get("mdo_valor", 0))
    pintura = dados.get("pintura", "none")
    pintura_horas = float(dados.get("pintura_horas", 0))
    risco_pct = valor(config, "RISCO_FALHAS_PCT", 10) / 100
    markup = float(dados.get("markup", 1.6))
    taxa_extra = float(dados.get("taxa_extra", 0))

    peso_total = peso * quantidade
    tempo_total = tempo * quantidade
    material = (peso_total / 1000) * filamento_kg
    energia = (
        valor(config, "POTENCIA_IMPRESSORA_W") / 1000
        * tempo_total
        * valor(config, "CUSTO_KWH")
    )

    vida_util = valor(config, "VIDA_UTIL_IMPRESSORA_HORAS")
    depreciacao = (
        valor(config, "VALOR_IMPRESSORA") / vida_util * tempo_total
        if vida_util else 0
    )
    consumiveis = valor(config, "CONSUMIVEIS_POR_HORA") * tempo_total
    mao_de_obra = mdo_horas * mdo_valor
    custo_direto = (
        material + energia + depreciacao + consumiveis + embalagem + mao_de_obra
    )

    custos_mensais = sum(valor(config, nome) for nome in (
        "ALUGUEL",
        "ASSINATURAS_SOFTWARES",
        "PLATAFORMAS_ECOMMERCE",
        "TAXA_MEI",
        "PUBLICIDADE_MINIMA_FIXA",
        "AMORTIZACAO",
        "CONDOMINIO",
        "OUTROS_CUSTOS_FIXOS",
    ))
    horas_produtivas = valor(config, "HORAS_PRODUTIVAS_MENSAIS", 1) or 1
    custo_fixo_por_hora = custos_mensais / horas_produtivas
    custo_fixo = custo_fixo_por_hora * tempo_total

    percentual_consumo = {
        "simples": valor(config, "CONSUMO_PINTURA_SIMPLES_PCT", 5),
        "media": valor(config, "CONSUMO_PINTURA_MEDIA_PCT", 10),
        "complexa": valor(config, "CONSUMO_PINTURA_COMPLEXA_PCT", 20),
    }.get(pintura, 0) / 100
    custo_pintura = 0
    if pintura != "none":
        valor_produtos_pintura = (
            valor(config, "TINTA_ACRILICA")
            + valor(config, "PRIMER")
            + valor(config, "VERNIZ")
        )
        materiais_pintura = (
            valor_produtos_pintura * percentual_consumo * quantidade
        )
        mao_de_obra_pintura = (
            pintura_horas * valor(config, "MAO_DE_OBRA_PINTURA_POR_HORA", 30)
        )
        custo_pintura = materiais_pintura + mao_de_obra_pintura

    subtotal = custo_direto + custo_fixo + custo_pintura + taxa_extra
    risco = subtotal * risco_pct
    custo_total = subtotal + risco
    preco = custo_total * markup
    lucro = preco - custo_total

    taxa_shopee = valor(config, "PERCENTUAL_SHOPEE", 20) / 100
    taxa_ml = valor(config, "PERCENTUAL_MERCADO_LIVRE", 19) / 100
    shopee = (preco + valor(config, "TAXA_FIXA_SHOPEE", 7)) / (1 - taxa_shopee)
    mercado_livre = preco / (1 - taxa_ml)

    def arredondar(numero):
        return round(numero, 2)

    return jsonify({
        "material": arredondar(material),
        "energia": arredondar(energia),
        "deprec": arredondar(depreciacao),
        "consumiveis": arredondar(consumiveis),
        "embalagem": arredondar(embalagem),
        "mdo_imp": arredondar(mao_de_obra),
        "fixo_diss": arredondar(custo_fixo),
        "pintura": arredondar(custo_pintura),
        "taxa_extra": arredondar(taxa_extra),
        "risco": arredondar(risco),
        "custo_total": arredondar(custo_total),
        "preco": arredondar(preco),
        "lucro": arredondar(lucro),
        "shopee": arredondar(shopee),
        "ml": arredondar(mercado_livre),
        "quantidade": quantidade,
        "preco_unitario": arredondar(preco / quantidade),
        "shopee_unitario": arredondar(shopee / quantidade),
        "ml_unitario": arredondar(mercado_livre / quantidade),
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Calc 3D - Bambu Estudio")
    print("  Acesse: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
