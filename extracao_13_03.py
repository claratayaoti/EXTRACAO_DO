import requests
import io
import fitz  # PyMuPDF para leitura de PDF
import re
import csv
from datetime import date

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
    print(f"Erro ao baixar o PDF: {response.status_code}")
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

    ## Expressões regulares
    regex_decreto = re.compile(
    r"DECRETO\s*N°\s*(\d+/\d{4})\s*"  # Captura o número do decreto
    r"(.*?)"  # Captura todo o conteúdo do decreto
    r"PREFEITURA\s*MUNICIPAL\s*DE\s*NITER[ÓO]I,\s*EM\s*\d{1,2}\s*DE\s*[A-Z]+\s*DE\s*\d{4}\.",
    re.DOTALL
    )

    # Nomeação
    regex_portaria_nomeacao = re.compile(
        r"Port\. Nº (\d+/\d+)\s*-\s*"  # Número da portaria
        r"\s*(Nomeia|Nomear)\s*"  # Tipo
        r"([\wÀ-ÿ\s,]+?)\s*"  # Nome
        r"para exercer o cargo de\s*([\wÀ-ÿ\s]+),\s*([\w\d\s-]+),\s*"  # Cargo e código
        r"(da|do)\s*([\wÀ-ÿ\s,]+?)\s*"  # Órgão
        r"(?:,\s*em\s*vaga\s*decorrente\s*da\s*exoneração\s*de\s*([\wÀ-ÿ\s]+))?"  # Vaga decorrente (opcional)
        r"(?:\s*,\s*acrescido\s*das\s*gratificações\s*previstas\s*na\s*CI\s*nº\s*(\d+/\d+))?\s*\.",  # Gratificações (opcional)
        re.DOTALL
    )

    # Exoneração
    regex_portaria_exoneracao = re.compile(
        r"Port\. Nº (\d+/\d+)\s*-\s*"  # Número da portaria
        r"(Exonera(?:,?\s*a\s*pedido)?|Exonerar,?\s*a\s*pedido?|Exonerar,?\s*a\s*contar\s*de\s*(\d{2}/\d{2}/\d{4})?|Exonera,\s*|Exonerar,\s*),?\s*"  # Tipo de exoneração
        r"([\wÀ-ÿ\s]+?),?\s*"  # Nome do exonerado
        r"do\s*cargo\s*(?:isolado\s*de\s*provimento\s*em\s*comissão,\s*)?"  # Cargo isolado (opcional)
        r"de\s*([\wÀ-ÿ\s]+),\s*símbolo\s*([\w\d-]+),\s*"  # Cargo e código do cargo
        r"(?:do\s*Quadro Permanente)?,\s*(?:da|do)\s*([\wÀ-ÿ\s,]+),"  # Órgão
        r"(?:\s*por ter sido nomead[oa]\s*para\s*cargo\s*([\wÀ-ÿ\s]+)\.)?",  # Motivo da exoneração (opcional)
        re.DOTALL
    )
     
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
        r"\s*onde se lê:\s*([\wÀ-ÿ\s,]+?)(,|\.)\s*"  # Nome original
        r"leia-se:\s*([\wÀ-ÿ\s,]+?)\.",  # Nome corrigido
        re.DOTALL
    )
    
    # Processamento de decretos
    for match in regex_decreto.finditer(texto):
        num_decreto = match.group(2)  # O número do decreto (ex: 224/2025)
        conteudo = match.group(1) + match.group(3)  # Junta "DECRETO N° xxx" + conteúdo + prefeitura
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
            "vaga_decorrente": resultado.group(8),
            "gratificacoes": resultado.group(9)
        })

    print("nomeacao:", portarias_nomeacao)

    # Processamento de portarias de exoneração
    for resultado in regex_portaria_exoneracao.finditer(texto):
        portarias_exoneracao.append({
            "num_portaria": resultado.group(1),
            "tipo": resultado.group(2),
            "nome": resultado.group(3),
            "cargo": resultado.group(4),
            "cod_cargo": resultado.group(5),
            "orgao": resultado.group(6)
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

    print("corrigenda:", portarias_corrigendas)

    return decretos, portarias_nomeacao, portarias_exoneracao, portarias_insubsistentes, portarias_corrigendas

def salvar_csv(decretos, portarias_nomeacao, portarias_exoneracao, portarias_insubsistentes, portarias_corrigendas):
    """Salva os decretos e portarias em arquivos CSV."""
    data_teste_str = data_teste.strftime("%d-%m-%Y")  # Formato DD-MM-AAAA
    with open(f"decretos_{data_teste_str}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Número", "Conteúdo"])
        writer.writeheader()
        writer.writerows(decretos)

    with open(f"portarias_nomeacao_{data_teste_str}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao", "vaga_decorrente", "gratificacoes"])
        writer.writeheader()
        writer.writerows(portarias_nomeacao)

    with open(f"portarias_exoneracao_{data_teste_str}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao"])
        writer.writeheader()
        writer.writerows(portarias_exoneracao)

    with open(f"portarias_insubsistentes_{data_teste_str}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["num_portaria", "portaria_insubsistente", "data_publicacao"])
        writer.writeheader()
        writer.writerows(portarias_insubsistentes)

    with open(f"portarias_corrigendas_{data_teste_str}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["num_portaria", "data_publicacao", "texto_anterior", "texto_corrigido"])
        writer.writeheader()
        writer.writerows(portarias_corrigendas)

# 🟢 Execução do Script
if __name__ == "__main__":
    data_teste = date(2025, 3, 15)  # Data de teste: 15/03/2025
    url = gerar_url_diario_oficial(data_teste)
    print(f"Baixando: {url}")
    if pdf_bytes := baixar_pdf(url):
        texto = extrair_texto_pdf(pdf_bytes)
        decretos, portarias_nomeacao, portarias_exoneracao, portarias_insubsistentes, portarias_corrigendas = segmentar_texto(texto)

        print(f"✅ {len(decretos)} decretos encontrados")
        print(f"✅ {len(portarias_nomeacao)} portarias de nomeação encontradas")
        print(f"✅ {len(portarias_exoneracao)} portarias de exoneração encontradas")
        print(f"✅ {len(portarias_insubsistentes)} portarias insubsistentes encontradas")
        print(f"✅ {len(portarias_corrigendas)} corrigendas encontradas")

        salvar_csv(decretos, portarias_nomeacao, portarias_exoneracao, portarias_insubsistentes, portarias_corrigendas)
        print("Arquivos gerados: decretos.csv, portarias_nomeacao.csv, portarias_exoneracao.csv, portarias_insubsistentes.csv, portarias_corrigendas.csv")
    else:
        print("❌ Não foi possível baixar o Diário Oficial de hoje.")