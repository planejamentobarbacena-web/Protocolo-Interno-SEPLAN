import pandas as pd
import os
from datetime import datetime
import pytz


def agora_br():
    tz = pytz.timezone("America/Sao_Paulo")
    return datetime.now(tz)


def registrar_andamento(
    id_processo,
    servidor,
    acao,
    observacao,
    setor_origem,
    setor_destino,
    perfil="Servidor"
):
    caminho = "data/andamentos.csv"

    colunas = [
        "id_andamento",
        "id_processo",
        "data",
        "servidor",
        "perfil",
        "acao",
        "observacao",
        "setor_origem",
        "setor_destino"
    ]

    if os.path.exists(caminho):
        df = pd.read_csv(caminho)

        # 🔒 GARANTIA DE COLUNAS
        for col in colunas:
            if col not in df.columns:
                df[col] = None
    else:
        df = pd.DataFrame(columns=colunas)

    # 🔢 ID seguro
    if df.empty or df["id_andamento"].isna().all():
        novo_id = 1
    else:
        novo_id = int(df["id_andamento"].dropna().max()) + 1

    novo = {
        "id_andamento": novo_id,
        "id_processo": id_processo,
        "data": agora_br(),
        "servidor": servidor,
        "perfil": perfil,
        "acao": acao,
        "observacao": observacao,
        "setor_origem": setor_origem,
        "setor_destino": setor_destino
    }

    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    df.to_csv(caminho, index=False)
