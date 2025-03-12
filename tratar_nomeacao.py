import csv

# Função para limpar quebras de linha e espaços extras
def limpar_campo(campo):
    if campo:
        return campo.replace("\n", " ").strip()
    return campo

# Ler o arquivo CSV original
with open("portarias_nomeacao.csv", "r", encoding="utf-8") as arquivo_entrada:
    leitor = csv.DictReader(arquivo_entrada)
    dados = [linha for linha in leitor]

# Tratar os dados
dados_tratados = []
for linha in dados:
    linha_tratada = {
        "num_portaria": limpar_campo(linha["num_portaria"]),
        "tipo": limpar_campo(linha["tipo"]),
        "nome": limpar_campo(linha["nome"]),
        "cargo": limpar_campo(linha["cargo"]),
        "cod_cargo": limpar_campo(linha["cod_cargo"]),
        "orgao": limpar_campo(linha["orgao"]),
        "vaga_decorrente": limpar_campo(linha["vaga_decorrente"]) or "N/A",
        "gratificacoes": limpar_campo(linha["gratificacoes"]) or "N/A"
    }
    dados_tratados.append(linha_tratada)

# Salvar os dados tratados em um novo arquivo CSV
with open("portarias_nomeacao_tratado.csv", "w", newline="", encoding="utf-8") as arquivo_saida:
    campos = ["num_portaria", "tipo", "nome", "cargo", "cod_cargo", "orgao", "vaga_decorrente", "gratificacoes"]
    escritor = csv.DictWriter(arquivo_saida, fieldnames=campos)
    escritor.writeheader()
    escritor.writerows(dados_tratados)

print("Dados tratados salvos em 'portarias_nomeacao_tratado.csv'.")