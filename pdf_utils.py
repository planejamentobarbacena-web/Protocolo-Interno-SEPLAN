from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib import colors
from datetime import datetime
import pandas as pd
import os

# ===============================
# BUSCAR NOME COMPLETO DO SERVIDOR
# ===============================

def obter_nome_completo(usuario):
    try:
        df_users = pd.read_csv("data/usuarios.csv")
        nome = df_users.loc[
            df_users["usuario"] == usuario, "nome_completo"
        ]
        return nome.iloc[0] if not nome.empty else usuario
    except Exception:
        return usuario


# ===============================
# FORMATADOR DE DATA
# ===============================

def formatar_data(data):
    if not data or pd.isna(data):
        return ""
    try:
        return pd.to_datetime(data).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(data)

# ===============================
# BUSCAR ENCAMINHAMENTO EXTERNO
# ===============================
def buscar_encaminhamento_externo(id_processo):
    try:
        df = pd.read_csv("data/destinacoes.csv")
        df = df[df["id_processo"] == id_processo]
        return df if not df.empty else None
    except Exception:
        return None

# ===============================
# RODAPÉ
# ===============================
def rodape(canvas, doc, usuario_emissor):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)

    texto = f"Emitido por: {usuario_emissor}"
    largura_pagina, _ = A4

    canvas.drawRightString(
        largura_pagina - 50,  # margem direita
        30,                   # altura do rodapé
        texto
    )

    canvas.restoreState()

# ===============================
# PDF DO PROCESSO
# ===============================

def gerar_pdf_processo(*, processo, historico, nome_arquivo, usuario_emissor):

    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=30,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Titulo",
        fontSize=14,
        leading=18,
        alignment=1,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="DataRelatorio",
        fontSize=10,
        leading=12,
        alignment=2,
        textColor=colors.grey
    ))

    styles.add(ParagraphStyle(
        name="Subtitulo",
        fontSize=11,
        leading=14,
        spaceAfter=10,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="CardTitulo",
        fontSize=11,
        leading=14,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="CardTexto",
        fontSize=11,
        leading=6,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        name="CardObservacao",
        fontSize=11,
        leading=16,
        spaceBefore=6,
        spaceAfter=4
    ))

    elementos = []

    # ===============================
    # LOGO INSTITUCIONAL
    # ===============================

    caminho_logo = os.path.join("assets", "logo.png")

    if os.path.exists(caminho_logo):
        logo = Image(
            caminho_logo,
            width=500,
            height=50
        )
        logo.hAlign = "CENTER"
        elementos.append(logo)
        elementos.append(Spacer(1, 12))

    # ===============================
    # TÍTULO
    # ===============================

    elementos.append(
        Paragraph("PROTOCOLO INTERNO - SEPLAN", styles["Titulo"])
    )

    data_emissao = datetime.now().strftime("%d/%m/%Y")
    elementos.append(
        Paragraph(f"Emitido em: {data_emissao}", styles["DataRelatorio"])
    )

    elementos.append(Spacer(1, 20))

    # ===============================
    # QUADRO PRINCIPAL DO PROCESSO
    # ===============================

    dados_table = [
        ["Protocolo:", processo.get("numero_protocolo", "")],
        ["Setor de Origem:", processo.get("setor_origem", "")],
        ["Setor Atual:", processo.get("setor_atual", "")],
        ["Número de Referência:", processo.get("numero_referencia", "")],
        ["Assunto do Processo:", processo.get("assunto", "")]
    ]

    tabela_dados = Table(dados_table, colWidths=[160, 310])

    tabela_dados.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(tabela_dados)
    elementos.append(Spacer(1, 24))

        # ===============================
    # ENCAMINHAMENTO EXTERNO
    # ===============================

    dest_ext = buscar_encaminhamento_externo(
        historico["id_processo"].iloc[0]
    )

    elementos.append(
        Paragraph("ENCAMINHAMENTO EXTERNO", styles["Subtitulo"])
    )

    if dest_ext is None:
        # Mensagem quando não há destinação
        elementos.append(
            Paragraph(
                "Este processo não possui encaminhamento externo.",
                styles["CardTexto"]
            )
        )
        elementos.append(Spacer(1, 16))

    else:
        for idx, (_, row) in enumerate(dest_ext.iterrows(), start=1):

            card_ext = Table(
                [
                    [Paragraph(
                        f"{idx}. Destinação Externa",
                        styles["CardTitulo"]
                    )],
                    [Paragraph(
                        f"<b>Data de Saída:</b> {formatar_data(row.get('data_saida'))}",
                        styles["CardTexto"]
                    )],
                    [Paragraph(
                        f"<b>Destino:</b> {row.get('destino','')}",
                        styles["CardTexto"]
                    )],
                    [Paragraph(
                        f"<b>Responsável:</b> {obter_nome_completo(row.get('protocolista',''))}",
                        styles["CardTexto"]
                    )],
                    [Paragraph(
                        f"<b>Observação:</b><br/>{row.get('observacao','')}",
                        styles["CardObservacao"]
                    )],
                ],
                colWidths=[470]
            )

            card_ext.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.75, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))

            elementos.append(card_ext)
            elementos.append(Spacer(1, 14))



    # ===============================
    # HISTÓRICO DE TRAMITAÇÃO
    # ===============================

    elementos.append(
        Paragraph("HISTÓRICO DE TRAMITAÇÃO", styles["Subtitulo"])
    )

    for idx, (_, row) in enumerate(historico.iterrows(), start=1):

        nome_servidor = obter_nome_completo(row.get("servidor", ""))

        card = Table(
            [
                [Paragraph(
                    f"{idx}. {row.get('setor_origem','')} → {row.get('setor_destino','')}",
                    styles["CardTitulo"]
                )],
                [Paragraph(
                    f"<b>Servidor:</b> {nome_servidor}",
                    styles["CardTexto"]
                )],
                [Paragraph(
                    f"<b>Data:</b> {formatar_data(row.get('data'))}",
                    styles["CardTexto"]
                )],
                [Paragraph(
                    f"<b>Ação:</b> {row.get('acao','')}",
                    styles["CardTexto"]
                )],
                [Paragraph(
                    f"<b>Observação:</b><br/>{row.get('observacao','')}",
                    styles["CardObservacao"]
                )],
            ],
            colWidths=[470]
        )

        card.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        elementos.append(card)
        elementos.append(Spacer(1, 14))


    doc.build(
        elementos,
        onFirstPage=lambda c, d: rodape(c, d, usuario_emissor),
        onLaterPages=lambda c, d: rodape(c, d, usuario_emissor)
    )


    return nome_arquivo