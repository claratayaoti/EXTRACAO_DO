import requests
import io
import fitz  # PyMuPDF para leitura de PDF
import re
import csv
from datetime import date, timedelta

# Dicionário para converter número do mês para nome abreviado
meses_portugues = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
}

def gerar_url_diario_oficial(data):
    """Gera a URL do Diário Oficial de Niterói para a data especificada."""
    ano = data.strftime("%Y")
    mes_numero = data.strftime("%m")
    dia = data.strftime("%d")
    mes_abreviado = meses_portugues[mes_numero]
    mes_extenso = f"{mes_numero}_{mes_abreviado}"
    return f"https://diariooficial.niteroi.rj.gov.br/do/{ano}/{mes_extenso}/{dia}.pdf"

def baixar_pdf(url):
    """Baixa o PDF do Diário Oficial e retorna um objeto BytesIO."""
    response = requests.get(url)
    if response.status_code == 200:
        return io.BytesIO(response.content)
    print(f"⚠️ Diário Oficial não encontrado para {url}")
    return None

def extrair_texto_pdf(pdf_bytes):
    """Extrai o texto do PDF como um único bloco de texto."""
    doc = fitz.open("pdf", pdf_bytes)
    texto = "\n".join(pagina.get_text("text") for pagina in doc)
    return pre_processar_texto(texto)

def pre_processar_texto(texto):
    """Remove cabeçalhos de página e ruídos do texto extraído."""
    linhas = texto.split("\n")
    texto_limpo = [linha for linha in linhas if not re.search(r"Página \d+", linha)]
    return "\n".join(texto_limpo)

def segmentar_texto(texto):
    """Segmenta o texto extraído em Decretos e Portarias."""
    decretos = []
    portarias_nomeacao = []
    portarias_exoneracao = []
    portarias_insubsistentes = []
    portarias_corrigendas = []

    # Expressões regulares
    regex_decreto = re.compile(
        r"DECRETO Nº (\d+/\d{4})\s*\n"  # Captura o número do decreto
        r"(.*?)"  # Captura todo o conteúdo do decreto
        r"PREFEITURA MUNICIPAL DE NITERÓI, EM \d{1,2} DE \w+ DE \d{4}\.",  # Captura a data final do decreto
        re.DOTALL
    )

    # Nomeação
    regex_portaria_nomeacao = re.compile(
        r"Port\. Nº (\d+/\d+)\s*-\s*"  # Número da portaria
        r"\s*(Nomeia|Nomear)\s*"  # Tipo
        r"([\wÀ-ÿ\s,]+?)\s*"  # Nome
        r"para exercer o cargo de\s*([\wÀ-ÿ\s]+),\s*([\w\d\s-]+),\s*"  # Cargo e código
        r"(da|do)\s*([\wÀ-ÿ\s,]+?)\s*"  # Órgão
        r"(?:\s*em\s*vaga\s*transferida\s*pelo\s*Decreto\s*Nº\s*(\d+/\d+))?" #Vaga transferida (opcional)
        r"(?:,\s*em\s*vaga\s*decorrente\s*da\s*exoneração\s*de\s*([\wÀ-ÿ\s]+))?"  # Vaga decorrente (opcional)
        r"(?:\s*,\s*acrescido\s*das\s*gratificações\s*previstas\s*na\s*CI\s*nº\s*(\d+/\d+))?\s*\.",  # Gratificações (opcional)
        re.DOTALL
    )

    # Exoneração
    regex_portaria_exoneracao = re.compile(
        r"Port\. Nº (\d+/\d+)\s*-\s*"  # Número da portaria
        r"(Exonera(?:,?\s*a\s*pedido)?|Exonerar,?\s*a\s*pedido?|Exonera,\s*|Exonerar,\s*),?\s*"  # Tipo de exoneração
        r"([\wÀ-ÿ\s]+?),?\s*"  # Nome do exonerado
        r"do\s*cargo\s*(?:isolado\s*de\s*provimento\s*em\s*comissão,\s*)?"  # Cargo isolado (opcional)
        r"de\s*([\wÀ-ÿ\s]+),\s*símbolo\s*([\w\d-]+),\s*"  # Cargo e código do cargo
        r"(?:do\s*Quadro Permanente)?,\s*(?:da|do)\s*([\wÀ-ÿ\s,]+),"  # Órgão
        r"(?:\s*por ter sido nomead[oa]\s*para\s*cargo\s*([\wÀ-ÿ\s]+)\.)?",  # Motivo da exoneração (opcional)
        re.DOTALL
    )
    
    """
    regex_portaria_exoneracao = re.compile(
        r"Port\. Nº (\d+/\d+)\s*-\s*(Exonera(?:,?\s*a\s*pedido)?|Exonerar,?\s*a\s*pedido?|Exonera,\s*|Exonerar,\s*),?\s*"  # Número da portaria e tipo de exoneração
        r"([\wÀ-ÿ\s]+?),?\s*"  # Nome do exonerado
        #r"(?do cargo isolado de provimento em comissão)?" # Cargo isolado
        r"do\s*cargo\s*de\s*([\wÀ-ÿ\s]+),\s*([\w\d\s-]+),\s*"  # Cargo e código
        r"(?:da|do)\s*([\wÀ-ÿ\s,]+)"  # Órgão
        r"(?:por ter sido nomeada para ([\wÀ-ÿ\s]+)\.)?", # Motivo da exoneração
        re.DOTALL
    )
    """
     # Torna insubsistente
    regex_insubsistente = re.compile(
        r"Port\. Nº (\d+/\d+)\s*-\s*"  # Número da portaria atual
        r"Torna (insubsistente|sem efeito) a (Portaria|Port.) (nº|Nº) (\d+/\d+),\s*"  # Número da portaria insubsistente
        r"publicada em (\d{2}/\d{2}/\d{4})\.?",  # Data de publicação
        re.DOTALL
    )

    # Corrigenda
    regex_substituicao = re.compile(
        r"Na Portaria nº (\d+/\d+),\s*"  # Número da portaria
        r"publicada em (\d{2}/\d{2}/\d{4}),\s*"  # Data de publicação
        r"onde se lê:\s*(.*?),\s*"  # Texto original (permitindo capturar sem aspas específicas)
        r"leia-se:\s*(.*?)\.",  # Texto corrigido
        re.DOTALL
    )

    # Processamento de decretos
    for match in regex_decreto.finditer(texto):
        num_decreto, conteudo = match.groups()
        decretos.append({
            "Número": num_decreto,
            "Conteúdo": conteudo.strip()
        })

    # Processamento de portarias de nomeação
    for resultado in regex_portaria_nomeacao.finditer(texto):
        portarias_nomeacao.append({
            "num_portaria": resultado.group(1),
            "tipo": resultado.group(2),
            "nome": resultado.group(3),
            "cargo": resultado.group(4),
            "cod_cargo": resultado.group(5),
            "orgao": resultado.group(7),
            "vaga_transferida": resultado.group(8),
            "vaga_decorrente": resultado.group(9),
            "gratificacoes": resultado.group(10)
        })

    # Processamento de portarias de exoneração
    for resultado in regex_portaria_exoneracao.finditer(texto):
        portarias_exoneracao.append({
            "num_portaria": resultado.group(1),
            "tipo": resultado.group(2),
            "nome": resultado.group(3),
            "cargo": resultado.group(4),
            "cod_cargo": resultado.group(5),
            "orgao": resultado.group(6),
            "motivo": resultado.group(7)
        })

    # Processamento de portarias insubsistentes
    for resultado in regex_insubsistente.finditer(texto):
        portarias_insubsistentes.append({
            "num_portaria": resultado.group(1),
            "portaria_insubsistente": resultado.group(5),
            "data_publicacao": resultado.group(6)
        })

    # Processamento de corrigendas
    for resultado in regex_substituicao.finditer(texto):
        portarias_corrigendas.append({
            "num_portaria": resultado.group(1),
            "data_publicacao": resultado.group(2),
            "texto_anterior": resultado.group(3),
            "texto_corrigido": resultado.group(4)
        })

    return decretos, portarias_nomeacao, portarias_exoneracao, portarias_insubsistentes, portarias_corrigendas

def salvar_csv(dados, nome_arquivo, campos):
    """Salva os dados em um arquivo CSV."""
    with open(nome_arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(dados)

# 🟢 Execução do Script
if __name__ == "__main__":
    data_inicio = date(2025, 1, 1)  # Data inicial: 01/01/2025
    data_fim = date.today()  # Data final: hoje

    # Listas para acumular os dados de todas as datas
    todos_decretos = []
    todas_portarias_nomeacao = []
    todas_portarias_exoneracao = []
    todas_portarias_insubsistentes = []
    todas_portarias_corrigendas = []

    # Iterar sobre todas as datas no intervalo
    data_atual = data_inicio
    while data_atual <= data_fim:
        url = gerar_url_diario_oficial(data_atual)
        print(f"Processando: {data_atual.strftime('%d/%m/%Y')} - {url}")

        pdf_bytes = baixar_pdf(url)
        if pdf_bytes:
            texto = extrair_texto_pdf(pdf_bytes)
            decretos, portarias_nomeacao, portarias_exoneracao, portarias_insubsistentes, portarias_corrigendas = segmentar_texto(texto)

            # Adicionar os dados às listas acumuladoras com a coluna "Data"
            for item in decretos:
                item["Data"] = data_atual.strftime("%d/%m/%Y")
            for item in portarias_nomeacao:
                item["Data"] = data_atual.strftime("%d/%m/%Y")
            for item in portarias_exoneracao:
                item["Data"] = data_atual.strftime("%d/%m/%Y")
            for item in portarias_insubsistentes:
                item["Data"] = data_atual.strftime("%d/%m/%Y")
            for item in portarias_corrigendas:
                item["Data"] = data_atual.strftime("%d/%m/%Y")

            # Adicionar os dados às listas acumuladoras
            todos_decretos.extend(decretos)
            todas_portarias_nomeacao.extend(portarias_nomeacao)
            todas_portarias_exoneracao.extend(portarias_exoneracao)
            todas_portarias_insubsistentes.extend(portarias_insubsistentes)
            todas_portarias_corrigendas.extend(portarias_corrigendas)

        else:
            # Se não houver edição, registrar no histórico
            print(f"⚠️ Não houve edição do Diário Oficial em {data_atual.strftime('%d/%m/%Y')}")
            todos_decretos.append({"Data": data_atual.strftime("%d/%m/%Y"), "Número": "N/A", "Conteúdo": "Não houve edição nesta data"})
            todas_portarias_nomeacao.append({"Data": data_atual.strftime("%d/%m/%Y"), "num_portaria": "N/A", "tipo": "N/A", "nome": "N/A", "cargo": "N/A", "cod_cargo": "N/A", "orgao": "N/A", "vaga_transferida": "N/A", "vaga_decorrente": "N/A", "gratificacoes": "N/A"})
            todas_portarias_exoneracao.append({"Data": data_atual.strftime("%d/%m/%Y"), "num_portaria": "N/A", "tipo": "N/A", "nome": "N/A", "cargo": "N/A", "cod_cargo": "N/A", "orgao": "N/A", "motivo": "N/A"})
            todas_portarias_insubsistentes.append({"Data": data_atual.strftime("%d/%m/%Y"), "num_portaria": "N/A", "portaria_insubsistente": "N/A", "data_publicacao": "N/A"})
            todas_portarias_corrigendas.append({"Data": data_atual.strftime("%d/%m/%Y"), "num_portaria": "N/A", "data_publicacao": "N/A", "texto_anterior": "N/A", "texto_corrigido": "N/A"})

        # Avançar para o próximo dia (fora do if/else)
        data_atual += timedelta(days=1)
        

    # Salvar os dados acumulados em arquivos CSV com a nova coluna "Data"
    salvar_csv(todos_decretos, "historico_decretos.csv", ["Data", "Número", "Conteúdo"])
    salvar_csv(todas_portarias_nomeacao, "historico_portarias_nomeacao.csv", ["Data", "num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao", "vaga_transferida", "vaga_decorrente", "gratificacoes"])
    salvar_csv(todas_portarias_exoneracao, "historico_portarias_exoneracao.csv", ["Data", "num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao", "motivo"])
    salvar_csv(todas_portarias_insubsistentes, "historico_portarias_insubsistentes.csv", ["Data", "num_portaria", "portaria_insubsistente", "data_publicacao"])
    salvar_csv(todas_portarias_corrigendas, "historico_portarias_corrigendas.csv", ["Data", "num_portaria", "data_publicacao", "texto_anterior", "texto_corrigido"])


    print("✅ Processamento concluído e arquivos CSV gerados com sucesso!")