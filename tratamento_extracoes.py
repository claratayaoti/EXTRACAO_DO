import csv
import datetime
import os

# Definir a data do arquivo no formato YYYY-MM-DD
data_hoje = datetime.date.today().strftime("%d-%m-%Y")  # Formato DD-MM-AAAA

# Função para limpar quebras de linha e espaços extras
def limpar_campo(campo):
    if campo:
        return campo.replace("\n", " ").strip()
    return campo

# Dicionário para definir os campos de cada arquivo
campos_arquivos = {
    "decretos": ["Número", "Conteúdo"],
    "portarias_nomeacao": ["num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao", "vaga_decorrente", "gratificacoes"],
    "portarias_exoneracao": ["num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao"],
    "portarias_insubsistentes": ["num_portaria", "portaria_insubsistente", "data_publicacao"],
    "portarias_corrigendas": ["num_portaria", "data_publicacao", "texto_anterior", "texto_corrigido"]
}

# Processar os arquivos
for tipo, campos in campos_arquivos.items():
    arquivo = f"{tipo}_{data_hoje}.csv"

    if os.path.exists(arquivo):  # Verifica se o arquivo existe antes de processá-lo
        try:
            # Ler o arquivo CSV original
            with open(arquivo, "r", encoding="utf-8") as arquivo_entrada:
                leitor = csv.DictReader(arquivo_entrada)
                dados = [linha for linha in leitor]

            # Tratar os dados
            dados_tratados = []
            for linha in dados:
                linha_tratada = {campo: limpar_campo(linha.get(campo, "")) for campo in campos}
                dados_tratados.append(linha_tratada)

            # Salvar os dados tratados em um novo arquivo
            nome_saida = f"{tipo}_tratado_{data_hoje}.csv"
            with open(nome_saida, "w", newline="", encoding="utf-8") as arquivo_saida:
                escritor = csv.DictWriter(arquivo_saida, fieldnames=campos)
                escritor.writeheader()
                escritor.writerows(dados_tratados)

            print(f"✅ Dados tratados salvos em '{nome_saida}'.")

        except Exception as e:
            print(f"⚠️ Erro ao processar '{arquivo}': {e}")

    else:
        print(f"⚠️ Arquivo '{arquivo}' não encontrado. Pulando para o próximo.")
