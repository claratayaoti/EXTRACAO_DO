import pandas as pd

# Caminho do arquivo CSV
csv_path = "decretos.csv"

# Carregar o CSV para verificar seu conteúdo
df = pd.read_csv(csv_path, encoding="utf-8")

# Exibir as primeiras linhas para entender a estrutura
print(df.head())

# Salvar o DataFrame em um arquivo Excel
excel_path = "decretos_tratados.xlsx"
df.to_excel(excel_path, index=False)

print(f"Planilha gerada com sucesso! O arquivo '{excel_path}' foi criado.")