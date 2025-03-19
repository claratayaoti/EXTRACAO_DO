import requests
import pdfplumber
import json
import io
import re
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

def pre_processar_texto(texto):
    """Remove cabeçalhos de página e ruídos do texto extraído."""
    linhas = texto.split("\n")
    texto_limpo = [linha for linha in linhas if not re.search(r"Página \d+", linha)]
    return "\n".join(texto_limpo)

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
        if "Port. Nº" in linhas[i]:
            # Inicializa as variáveis
            num_portaria = ""
            tipo = ""
            nome = ""
            cargo = ""
            codigo_cargo = ""
            orgao = ""
            vaga_exoneracao = ""
            vaga_transferida = ""
            descricao = ""

            # Extrai o número da portaria (remove o "-" no final, se houver)
            num_portaria = linhas[i].split("Port. Nº")[1].split()[0].strip().rstrip("-")

            # Extrai o tipo da portaria (Nomeia, Exonera, Torna insubsistente)
            if "Nomeia" in linhas[i] or "Nomear" in linhas[i]:
                tipo = "Nomeação"
            elif "Exonera" in linhas[i] or "Exonerar" in linhas[i]:
                tipo = "Exoneração"
            else:
                tipo = "Outro"

            # Concatena as linhas seguintes até encontrar a próxima portaria ou "SECRETARIA MUNICIPAL"
            texto_portaria = linhas[i].strip()
            j = i + 1
            while j < len(linhas):
                if "Port. Nº" in linhas[j] or "SECRETARIA MUNICIPAL" in linhas[j]:
                    break  # Para de concatenar se encontrar outra portaria ou "SECRETARIA MUNICIPAL"
                texto_portaria += " " + linhas[j].strip()
                j += 1
            
            # Armazena o texto completo da portaria no campo "descricao"
            descricao = texto_portaria

            # Extrai o nome da pessoa
            if tipo == "Nomeação":
                partes_nome = texto_portaria.split("Nomeia")
                if len(partes_nome) > 1:
                    nome = partes_nome[1].split("para exercer")[0].strip()
            elif tipo == "Exoneração":
                partes_nome = texto_portaria.split("Exonera")
                if len(partes_nome) > 1:
                    nome = partes_nome[1].split("do cargo")[0].strip().split(",")[-1].strip()

            # Extrai o cargo e o código do cargo
            if "do cargo de" in texto_portaria:
                cargo_completo = texto_portaria.split("do cargo de")[1].split(",")[0].strip()
                cargo_completo = re.sub(r'\s+', ' ', cargo_completo)  # Remove espaços extras
                if "-" in cargo_completo:
                    cargo = cargo_completo.split(",")[0].strip()
                    codigo_cargo = cargo_completo.split(",")[1].strip()
                else:
                    cargo = cargo_completo

            # Extrai o órgão
            if "da Secretaria" in texto_portaria:
                orgao = "Secretaria " + texto_portaria.split("da Secretaria")[1].split(",")[0].strip()
            elif "do Gabinete" in texto_portaria:
                orgao = "Gabinete " + texto_portaria.split("do Gabinete")[1].split(",")[0].strip()
            elif "da Gabinete" in texto_portaria:
                orgao = "Gabinete " + texto_portaria.split("da Gabinete")[1].split(",")[0].strip()
            elif "da Fundação" in texto_portaria:
                orgao = "Fundação " + texto_portaria.split("da Fundação")[1].split(",")[0].strip()
            elif "da Administração Regional" in texto_portaria:
                orgao = "Administração Regional " + texto_portaria.split("da Administração Regional")[1].split(",")[0].strip()

            # Captura informações específicas para cada tipo de portaria
            if "em vaga decorrente da exoneração de" in texto_portaria:
                vaga_exoneracao = texto_portaria.split("em vaga decorrente da exoneração de")[1].strip().split(",")[0].strip()
            if "em vaga transferida pelo Decreto" in texto_portaria:
                vaga_transferida = texto_portaria.split("em vaga transferida pelo Decreto")[1].strip().split(",")[0].strip()

            # Adiciona a portaria à lista
            portarias.append({
                "Número": num_portaria,
                "Tipo": tipo,
                "Nome": nome,
                "Cargo": cargo,
                "Código do Cargo": codigo_cargo,
                "Órgão": orgao,
                "Vaga Decorrente da Exoneração": vaga_exoneracao,
                "Vaga Transferida pelo Decreto": vaga_transferida,
                "Descrição": descricao
            })

            # Atualiza o índice para pular as linhas já processadas
            i = j
        else:
            i += 1
    return portarias

def buscar_insubsistentes(texto):
    """Busca portarias insubsistentes no texto usando lógica de programação."""
    insubsistentes = []
    linhas = texto.split("\n")
    i = 0
    while i < len(linhas):
        linha = linhas[i].strip()
        
        # Verifica se a linha contém "Torna insubsistente" ou "Torna sem efeito"
        if "torna insubsistente" in linha.lower() or "torna sem efeito" in linha.lower():
            # Extrai o número da portaria atual
            if "port. nº" in linha.lower():
                num_portaria = linha.split("Port. Nº")[1].split()[0].strip().rstrip("-")
            else:
                num_portaria = ""

            # Extrai o número da portaria insubsistente
            if "portaria nº" in linha.lower():
                portaria_insubsistente = linha.split("Portaria nº")[1].split(",")[0].strip()
            else:
                portaria_insubsistente = ""

            # Extrai a data de publicação
            if "publicada em" in linha.lower():
                data_publicacao = linha.split("publicada em")[1].split(".")[0].strip()
            else:
                data_publicacao = ""

            # Adiciona a portaria insubsistente à lista
            insubsistentes.append({
                "Número da Portaria": num_portaria,
                "Portaria Insubsistente": portaria_insubsistente,
                "Data de Publicação": data_publicacao
            })
        i += 1
    return insubsistentes

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
        insubsistentes = buscar_insubsistentes(texto)

        # Salva os resultados em JSON
        resultados = {
            "Decretos": decretos,
            "Portarias": portarias,
            "Corrigendas": corrigendas,
            "Insubsistentes": insubsistentes
        }
        nome_arquivo = f"diario_oficial_{hoje.strftime('%d-%m-%Y')}.json"
        salvar_json(resultados, nome_arquivo)
        print(f"✅ Dados salvos em {nome_arquivo}")
    else:
        print("❌ Não foi possível baixar o Diário Oficial de hoje.")