from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
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
# FORMATADOR DE DATA/HORA
# ===============================
def formatar_data_hora(data):
    if not data or pd.isna(data):
        return ""
    try:
        return pd.to_datetime(data).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(data)


# ===============================
# BUSCAR DADOS DO PROCESSO
# ===============================
def buscar_dados_processo(id_processo):
    try:
        df = pd.read_csv("data/processos.csv")
        dados = df[df["id_processo"] == id_processo]

        if dados.empty:
            return str(id_processo)

        row = dados.iloc[0]
        numero = str(row.get("numero_protocolo", "")).strip()
        assunto = str(row.get("assunto", "")).strip()

        if numero and assunto:
            return f"{numero} - {assunto}"
        elif numero:
            return numero
        elif assunto:
            return assunto
        else:
            return str(id_processo)

    except Exception:
        return str(id_processo)


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
        largura_pagina - 50,
        30,
        texto
    )

    canvas.restoreState()


# ===============================
# CARD PADRÃO
# ===============================
def criar_card(conteudo, largura):
    tabela = Table([[conteudo]], colWidths=[largura])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    return tabela


# ===============================
# GERAR PDF 4 – HISTÓRICO DO SERVIDOR
# ===============================
def gerar_pdf_4(
    servidor,
    historico,
    nome_arquivo,
    tipo_relatorio,
    logo_path,
    *,
    usuario_emissor
):

    nome_completo_servidor = obter_nome_completo(servidor)

    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=30,
        bottomMargin=50
    )

    largura_card = A4[0] - 100

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Titulo",
        fontSize=16,
        leading=20,
        alignment=1,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="Subtitulo",
        fontSize=12,
        leading=14,
        spaceBefore=14,
        spaceAfter=12,
        fontName="Helvetica-Bold"
    ))

    styles.add(ParagraphStyle(
        name="DataRelatorio",
        fontSize=9,
        leading=12,
        alignment=2,
        textColor=colors.grey
    ))

    styles.add(ParagraphStyle(
        name="CardTexto",
        fontSize=10,
        leading=14
    ))

    elementos = []

    # ===============================
    # LOGO
    # ===============================
    caminho_logo = logo_path

    if not caminho_logo or not os.path.exists(caminho_logo):
        caminho_logo = os.path.join("assets", "logo.png")

    if os.path.exists(caminho_logo):
        logo = Image(caminho_logo, width=500, height=50)
        logo.hAlign = "CENTER"
        elementos.append(logo)
        elementos.append(Spacer(1, 12))

    # ===============================
    # CABEÇALHO
    # ===============================
    elementos.append(
        Paragraph("HISTÓRICO DE ATUAÇÃO DO SERVIDOR", styles["Titulo"])
    )

    elementos.append(Spacer(1, 14))

    elementos.append(
        Paragraph(f"Servidor: {nome_completo_servidor}", styles["Subtitulo"])
    )

    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")
    elementos.append(
        Paragraph(f"Emitido em: {data_emissao}", styles["DataRelatorio"])
    )

    elementos.append(Spacer(1, 20))

    # ===============================
    # ORDENAÇÃO
    # ===============================
    if tipo_relatorio == "por_momento":
        historico = historico.sort_values("data")
    elif tipo_relatorio == "por_processo":
        historico = historico.sort_values(["id_processo", "data"])
    else:
        raise ValueError("tipo_relatorio inválido")

    # ===============================
    # CONTEÚDO
    # ===============================
    if tipo_relatorio == "por_processo":

        for proc in historico["id_processo"].dropna().unique():

            dados_proc = historico[historico["id_processo"] == proc]
            identificacao = buscar_dados_processo(proc)

            elementos.append(
                Paragraph(f"Processo: {identificacao}", styles["Subtitulo"])
            )

            for _, row in dados_proc.iterrows():

                conteudo = Paragraph(
                    f"""
                    <b>Data/Hora:</b> {formatar_data_hora(row.get('data'))}<br/>
                    <b>Ação:</b> {row.get('acao','')}<br/>
                    <b>Observação:</b> {row.get('observacao','')}<br/>
                    <b>Setor anterior:</b> {row.get('setor_origem','')}<br/>
                    <b>Setor atual:</b> {row.get('setor_destino','')}
                    """,
                    styles["CardTexto"]
                )

                elementos.append(criar_card(conteudo, largura_card))
                elementos.append(Spacer(1, 10))

    else:

        for _, row in historico.iterrows():

            identificacao = buscar_dados_processo(row.get("id_processo"))

            conteudo = Paragraph(
                f"""
                <b>Data/Hora:</b> {formatar_data_hora(row.get('data'))}<br/>
                <b>Processo:</b> {identificacao}<br/>
                <b>Ação:</b> {row.get('acao','')}<br/>
                <b>Observação:</b> {row.get('observacao','')}<br/>
                <b>Setor anterior:</b> {row.get('setor_origem','')}<br/>
                <b>Setor atual:</b> {row.get('setor_destino','')}
                """,
                styles["CardTexto"]
            )

            elementos.append(criar_card(conteudo, largura_card))
            elementos.append(Spacer(1, 10))

    # ===============================
    # BUILD
    # ===============================
    doc.build(
        elementos,
        onFirstPage=lambda c, d: rodape(c, d, usuario_emissor),
        onLaterPages=lambda c, d: rodape(c, d, usuario_emissor)
    )

    return nome_arquivo
