import json

# Função para extrair o cargo e o código do cargo da descrição
def extrair_cargo_e_codigo(descricao):
    if "para exercer o cargo de" in descricao:
        partes = descricao.split("para exercer o cargo de")[1].split(",")
        cargo = partes[0].strip()
        codigo_cargo = partes[1].strip() if len(partes) > 1 else ""
        return cargo, codigo_cargo
    return "", ""

# Carregar o arquivo JSON original
with open('portarias_01-01-2025_a_19-03-2025.json', 'r', encoding='utf-8') as file:
    portarias = json.load(file)

# Tratar cada portaria
for portaria in portarias:
    descricao = portaria["Descrição"]
    cargo, codigo_cargo = extrair_cargo_e_codigo(descricao)
    portaria["Cargo"] = cargo
    portaria["Código do Cargo"] = codigo_cargo

# Salvar o arquivo JSON tratado
with open('portarias_tratadas.json', 'w', encoding='utf-8') as file:
    json.dump(portarias, file, ensure_ascii=False, indent=4)

print("Arquivo JSON tratado salvo como 'portarias_tratadas.json'")