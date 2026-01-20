from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
from collections import defaultdict
import os


def gerar_pdf_remessa_multi_setor(processos, caminho_pdf, logo_path=None):
    """
    processos: lista de dicionários com:
        - setor_destino
        - numero_protocolo
        - numero_referencia
        - assunto
    """

    doc = SimpleDocTemplate(
        caminho_pdf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # ===============================
    # ESTILOS PERSONALIZADOS
    # ===============================
    styles.add(ParagraphStyle(
        name="TituloRemessa",
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=1,  # centro
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="DataDireita",
        fontName="Helvetica",
        fontSize=9,
        alignment=2,  # direita
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name="SetorTitulo",
        fontName="Helvetica-Bold",
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6
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
        elementos.append(Spacer(1, 10))

    # ===============================
    # CABEÇALHO
    # ===============================
    elementos.append(
        Paragraph("REMESSA DE ENVIO DE PROCESSOS", styles["TituloRemessa"])
    )

    elementos.append(
        Paragraph(
            f"Data de Emissão: {datetime.now().strftime('%d/%m/%Y')}",
            styles["DataDireita"]
        )
    )

    # ===============================
    # AGRUPAMENTO POR SETOR
    # ===============================
    agrupados = defaultdict(list)
    for p in processos:
        agrupados[p["setor_destino"]].append(p)

    # ===============================
    # TABELAS POR SETOR
    # ===============================
    for setor, itens in agrupados.items():

        elementos.append(
            Paragraph(f"SETOR DESTINO: {setor}", styles["SetorTitulo"])
        )

        dados = [[
            "Setor Destino",
            "Processo",
            "Referência",
            "Assunto",
            "Recebido por:",
            "Data"
        ]]

        for p in itens:
            dados.append([
                setor,
                p["numero_protocolo"],
                p["numero_referencia"],
                p["assunto"],
                "",
                ""
            ])

        tabela = Table(
            dados,
            repeatRows=1,
            colWidths=[80, 70, 90, 160, 80, 70]
        )

        tabela.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 1), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))

        elementos.append(tabela)

    # ===============================
    # BUILD
    # ===============================
    doc.build(elementos)
