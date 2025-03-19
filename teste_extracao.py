import requests
import pdfplumber
import json
import io
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
    """Extrai o texto do PDF usando pdfplumber."""
    texto = ""
    with pdfplumber.open(pdf_bytes) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text()
    return texto

def buscar_decretos(texto):
    """Busca decretos no texto usando lógica de programação."""
    decretos = []
    linhas = texto.split("\n")
    i = 0
    while i < len(linhas):
        if "DECRETO N°" in linhas[i]:
            num_decreto = linhas[i].split("DECRETO N°")[1].strip()
            conteudo = []
            anexo = []
            i += 1
            while i < len(linhas) and "PREFEITURA MUNICIPAL DE NITERÓI" not in linhas[i]:
                conteudo.append(linhas[i].strip())
                i += 1
            # Verifica se há anexo
            if i < len(linhas) and "ANEXO AO DECRETO Nº" in linhas[i]:
                i += 1
                while i < len(linhas) and "DECRETO N°" not in linhas[i] and "PREFEITURA MUNICIPAL DE NITERÓI" not in linhas[i]:
                    anexo.append(linhas[i].strip())
                    i += 1
            decretos.append({
                "Número": num_decreto,
                "Texto": " ".join(conteudo),
                "Anexo": " ".join(anexo)
            })
        else:
            i += 1
    return decretos

def buscar_portarias(texto):
    """Busca portarias no texto usando lógica de programação."""
    portarias = []
    linhas = texto.split("\n")
    i = 0
    while i < len(linhas):
        if "Port. Nº" in linhas[i]:  # Corrigido para "Port. Nº"
            partes = linhas[i].split(" - ")
            if len(partes) > 1:
                num_portaria = partes[0].split("Port. Nº")[1].strip()
                tipo = partes[1].strip()
                nome = ""
                cargo = ""
                codigo_cargo = ""
                orgao = ""
                vaga_exoneracao = ""
                vaga_transferida = ""

                # Captura o nome, cargo, código do cargo e órgão
                # Ajuste para capturar informações corretamente
                if i + 1 < len(linhas):
                    nome = linhas[i + 1].strip()
                if i + 2 < len(linhas):
                    cargo = linhas[i + 2].strip()
                if i + 3 < len(linhas):
                    codigo_cargo = linhas[i + 3].strip()
                if i + 4 < len(linhas):
                    orgao = linhas[i + 4].strip()

                # Captura informações específicas para cada tipo de portaria
                if "Nomeia" in tipo or "Nomear" in tipo:
                    # Captura vaga decorrente da exoneração ou transferida pelo Decreto
                    if "em vaga decorrente da exoneração de" in linhas[i + 1]:
                        vaga_exoneracao = linhas[i + 1].split("em vaga decorrente da exoneração de")[1].strip().split(",")[0].strip()
                    if "em vaga transferida pelo Decreto" in linhas[i + 1]:
                        vaga_transferida = linhas[i + 1].split("em vaga transferida pelo Decreto")[1].strip().split(",")[0].strip()
                elif "Exonera" in tipo or "Exonerar" in tipo:
                    # Captura vaga decorrente da exoneração
                    if "em vaga decorrente da exoneração de" in linhas[i + 1]:
                        vaga_exoneracao = linhas[i + 1].split("em vaga decorrente da exoneração de")[1].strip().split(",")[0].strip()
                elif "Torna insubsistente" in tipo:
                    # Não há informações adicionais para capturar
                    pass

                portarias.append({
                    "Número": num_portaria,
                    "Tipo": tipo,
                    "Nome": nome,
                    "Cargo": cargo,
                    "Código do Cargo": codigo_cargo,
                    "Órgão": orgao,
                    "Vaga Decorrente da Exoneração": vaga_exoneracao,
                    "Vaga Transferida pelo Decreto": vaga_transferida
                })
                i += 5  # Avança 5 linhas após a portaria
            else:
                print(f"Delimitador não encontrado na linha: {linhas[i]}")
                i += 1
        else:
            i += 1
    return portarias

def buscar_corrigendas(texto):
    """Busca corrigendas no texto usando lógica de programação."""
    corrigendas = []
    linhas = texto.split("\n")
    i = 0
    while i < len(linhas):
        if "Na Portaria nº" in linhas[i]:
            num_portaria = linhas[i].split("Na Portaria nº")[1].split(",")[0].strip()
            data_publicacao = linhas[i].split("publicada em")[1].split(",")[0].strip()
            # Check if "onde se lê:" is present before splitting and accessing the element
            if "onde se lê:" in linhas[i+1]:
                texto_anterior = linhas[i+1].split("onde se lê:")[1].strip()
            else:
                texto_anterior = ""  # Or handle the case differently, like skipping this corrigenda
            # Similarly, check for "leia-se:"
            if "leia-se:" in linhas[i+2]:
                texto_corrigido = linhas[i+2].split("leia-se:")[1].strip()
            else:
                texto_corrigido = "" # Or handle the case differently, like skipping this corrigenda

            corrigendas.append({
                "Número da Portaria": num_portaria,
                "Data de Publicação": data_publicacao,
                "Texto Anterior": texto_anterior,
                "Texto Corrigido": texto_corrigido
            })
            i += 3
        i += 1
    return corrigendas

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

        # Busca decretos, portarias e corrigendas
        decretos = buscar_decretos(texto)
        portarias = buscar_portarias(texto)
        corrigendas = buscar_corrigendas(texto)

        # Salva os resultados em JSON
        resultados = {
            "Decretos": decretos,
            "Portarias": portarias,
            "Corrigendas": corrigendas
        }
        nome_arquivo = f"diario_oficial_{hoje.strftime('%d-%m-%Y')}.json"
        salvar_json(resultados, nome_arquivo)
        print(f"✅ Dados salvos em {nome_arquivo}")
    else:
        print("❌ Não foi possível baixar o Diário Oficial de hoje.")