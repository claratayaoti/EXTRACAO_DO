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
    texto_limpo = []
    for linha in linhas:
        if not re.search(r"Página \d+", linha):  # Remove cabeçalhos com número de página
            texto_limpo.append(linha)
    return "\n".join(texto_limpo)

def segmentar_texto(texto):
    """Segmenta o texto extraído em Decretos e Portarias."""
    decretos = []
    portarias = []
    
    # Expressões regulares para capturar Decretos e Portarias
    regex_decreto = re.compile(
    r"DECRETO Nº (\d+/\d{4})\s*\n"  # Captura o número do decreto
    r"(.*?)"  # Captura todo o conteúdo do decreto
    r"PREFEITURA MUNICIPAL DE NITERÓI, EM \d{1,2} DE \w+ DE \d{4}\.",  # Captura a data final do decreto
    re.DOTALL
)
    
    regex_portaria = re.compile(
        r"Port\. Nº (\d+/\d+)-\s*(Nomeia|Nomear|Exonera|Exonerar?,\s*a\s*pedido,?)\s*"  # Número e tipo
        r"([\wÀ-ÿ\s]+?)\s*para exercer o cargo de\s*([\wÀ-ÿ\s]+?),?\s*"  # Nome e cargo
        r"([A-Z]+-?\d*)?,?\s*(da|do)\s*([\wÀ-ÿ\s]+),"  # Código do cargo (opcional) e órgão
        r"\s*?em vaga decorrente da exoneração de\s*([\wÀ-ÿ\s]+),?"  # Nome do exonerado
    )
    
    for match in regex_decreto.finditer(texto):
        num_decreto, conteudo = match.groups()
        decretos.append({
            "Número": num_decreto or "",
            "Conteúdo": conteudo.strip()
        })
        
    if match:
        num_decreto, conteudo = match.groups()
    print(f"Número do Decreto: {num_decreto}")
    print(f"Conteúdo:\n{conteudo[:500]}...")
    
    for match in regex_portaria.finditer(texto):
        num_portaria, tipo, nome, cargo, codigo, _, orgao, vaga_decorrente = match.groups()
        portarias.append({
            "Número": num_portaria,
            "Tipo": "Nomeação" if "Nomeia" in tipo or "Nomear" in tipo else "Exoneração",
            "Nome": nome.strip(),
            "Cargo": cargo.strip(),
            "Código": codigo.strip() if codigo else "",
            "Órgão": orgao.strip(),
            "Vaga Decorrente": vaga_decorrente.strip()
        })
    
    return decretos, portarias

def salvar_csv(decretos, portarias):
    """Salva os decretos e portarias em arquivos CSV."""
    with open("decretos.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Número", "Conteúdo"])
        writer.writeheader()
        writer.writerows(decretos)
        import pandas as pd

        
    with open("portarias.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Número", "Tipo", "Nome", "Cargo", "Código", "Órgão", "Vaga Decorrente"])
        writer.writeheader()
        writer.writerows(portarias)

# 🟢 Execução do Script
if __name__ == "__main__":
    hoje = date.today()
    url = gerar_url_diario_oficial(hoje)
    print(f"Baixando: {url}")
    if pdf_bytes := baixar_pdf(url):
        texto = extrair_texto_pdf(pdf_bytes)
        decretos, portarias = segmentar_texto(texto)

        print(f"✅ {len(decretos)} decretos encontrados")
        print(f"✅ {len(portarias)} portarias encontradas")

        salvar_csv(decretos, portarias)
        print("Arquivos gerados: decretos.csv, portarias.csv")
    else:
        print("❌ Não foi possível baixar o Diário Oficial de hoje.")
