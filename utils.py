import pandas as pd
from datetime import datetime
import os


def registrar_andamento(
    id_processo,
    servidor,
    acao,
    observacao,
    setor_origem,
    setor_destino
):
    caminho = "data/andamentos.csv"

    if os.path.exists(caminho):
        df = pd.read_csv(caminho)
    else:
        df = pd.DataFrame(columns=[
            "id_andamento",
            "id_processo",
            "data",
            "servidor",
            "acao",
            "observacao",
            "setor_origem",
            "setor_destino",
            "tempo_min"
        ])

    novo_id = int(df["id_andamento"].max() + 1) if not df.empty else 1

    novo = {
        "id_andamento": novo_id,
        "id_processo": id_processo,
        "data": datetime.now(),
        "servidor": servidor,
        "acao": acao,
        "observacao": observacao,
        "setor_origem": setor_origem,
        "setor_destino": setor_destino,
        "tempo_min": 0
    }

    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    df.to_csv(caminho, index=False)
