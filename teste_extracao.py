import requests
import pdfplumber
import spacy
import json
from datetime import date

# Carrega o modelo de linguagem em português
nlp = spacy.load("pt_core_news_sm")

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
    """Extrai o texto do PDF usando pdfplumber."""
    texto = ""
    with pdfplumber.open(pdf_bytes) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text()
    return texto

def processar_texto_com_nlp(texto):
    """Processa o texto usando spaCy para extrair informações."""
    doc = nlp(texto)
    resultados = []

    # Exemplo: Extrair nomes, cargos e órgãos
    for sent in doc.sents:
        entidades = {
            "PESSOA": [],
            "CARGO": [],
            "ORGÃO": [],
            "PORTARIA": None,
            "DECRETO": None
        }

        # Identifica entidades nomeadas
        for ent in sent.ents:
            if ent.label_ == "PER":  # Pessoas
                entidades["PESSOA"].append(ent.text)
            elif ent.label_ == "ORG":  # Órgãos
                entidades["ORGÃO"].append(ent.text)
            elif "cargo" in ent.text.lower():  # Cargos
                entidades["CARGO"].append(ent.text)

        # Identifica portarias e decretos
        if "Portaria" in sent.text:
            entidades["PORTARIA"] = sent.text
        elif "Decreto" in sent.text:
            entidades["DECRETO"] = sent.text

        resultados.append(entidades)

    return resultados

def salvar_json(resultados, nome_arquivo):
    """Salva os resultados em um arquivo JSON."""
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)

# 🟢 Execução do Script
if __name__ == "__main__":
    hoje = date.today()
    url = gerar_url_diario_oficial(hoje)
    print(f"Baixando: {url}")

    if pdf_bytes := baixar_pdf(url):
        texto = extrair_texto_pdf(pdf_bytes)
        resultados = processar_texto_com_nlp(texto)

        # Salva os resultados em JSON
        nome_arquivo = f"diario_oficial_{hoje.strftime('%d-%m-%Y')}.json"
        salvar_json(resultados, nome_arquivo)
        print(f"✅ Dados salvos em {nome_arquivo}")
    else:
        print("❌ Não foi possível baixar o Diário Oficial de hoje.")