# Importações
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import openpyxl
import os
import re 

load_dotenv()

# Importando os caminhos
BASE_PATH = os.getenv("BASE_PATH")
RAW_DATA_PATH = os.path.join(BASE_PATH, os.getenv("RAW_DATA_PATH"))
PROCESSED_DATA_PATH = os.path.join(BASE_PATH, os.getenv("PROCESSED_DATA_PATH"))

# Funções
def get_data():
    if not os.path.exists(RAW_DATA_PATH):
        print(f"Diretório não encontrado: {RAW_DATA_PATH}")
        return []
    arquivos = [f for f in os.listdir(RAW_DATA_PATH) if f.endswith('.csv')]
    return arquivos

# 1 - Etapa do pré-processamento
def pre_process(arquivos: list[str]):
    if not arquivos:
        print("Nenhum arquivo encontrado para processamento.")
        return

    for arquivo in arquivos:
        print(f"Iniciando processamento do arquivo: {arquivo}")
        caminho_completo = os.path.join(RAW_DATA_PATH, arquivo)
        
        try:
            match = re.search(r'(\d{4})', arquivo)
            ano_arquivo = int(match.group(1)) if match else 2000 

            # 1. Leitura do arquivo
            data = pd.read_csv(
                caminho_completo, 
                header=0, 
                sep=";", 
                encoding="latin1", 
                dtype={5: str, 6: str}
            )

            # 2. Limpeza Geral (Aplicável a todos os anos)
            data.replace('(null)', np.nan, inplace=True)
            data.replace('N/A', np.nan, inplace=True)
            
            if "id" in data.columns:
                data = data.drop(columns=["id"])

            colunas_para_string = [
                "uf", "br", "km", "municipio", "causa_acidente", "tipo_acidente",
                "classificacao_acidente", "fase_dia", "sentido_via",
                "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo"
            ]
            
            colunas_existentes = [col for col in colunas_para_string if col in data.columns]
            data[colunas_existentes] = data[colunas_existentes].astype('string')

            if 'data_inversa' in data.columns:
                data['data_inversa'] = pd.to_datetime(data['data_inversa'], format='%d/%m/%Y', errors='coerce')
            
            if 'horario' in data.columns:
                data['horario'] = pd.to_datetime(data['horario'], format='%H:%M:%S', errors='coerce').dt.time

            if 'dia_semana' in data.columns:
                data['dia_semana'] = data['dia_semana'].astype('category')
                finais_de_semana = ['sábado', 'sabado', 'domingo', 'Sábado', 'Sabado', 'Domingo']
                data['fim_de_semana'] = data['dia_semana'].isin(finais_de_semana).astype(int)

            # Tratamento do KM numérico (Corrigido com pd.to_numeric)
            if 'km' in data.columns:
                data["km"] = pd.to_numeric(data["km"].astype(str).str.replace(",", "."), errors='coerce')

            # 3. Tratamento condicional: IF / ELSE para anos >= 2017
            if ano_arquivo >= 2017:
                print(f" -> Aplicando regras de novas colunas para o ano {ano_arquivo}...")
                
                # Corrigido: Reatribuição simples sem inplace no método de string
                if "delegacia" in data.columns:
                    data["delegacia"] = data["delegacia"].replace("N/A", np.nan)
                if "uop" in data.columns:
                    data["uop"] = data["uop"].replace("N/A", np.nan)

                # Tratando long e lat (Corrigido com pd.to_numeric)
                if 'latitude' in data.columns and 'longitude' in data.columns:
                    data['latitude'] = pd.to_numeric(data['latitude'].astype(str).str.replace(',', '.'), errors='coerce')
                    data['longitude'] = pd.to_numeric(data['longitude'].astype(str).str.replace(',', '.'), errors='coerce')
                    
                    data = data.dropna(subset=['latitude', 'longitude'])  
                    
                    data = data[
                        (data['latitude'] >= -90) & (data['latitude'] <= 90) &
                        (data['longitude'] >= -180) & (data['longitude'] <= 180)
                    ]

            else:
                print(f" -> Estrutura antiga ({ano_arquivo}).")
                data["latitude"] = pd.NA
                data["longitude"] = pd.NA
                data["regional"] = pd.NA
                data["delegacia"] = pd.NA
                data["uop"] = pd.NA            

            # 4. Salvando o dado processado
            arquivo_saida = f"processed_{arquivo}"
            caminho_saida = os.path.join(PROCESSED_DATA_PATH, arquivo_saida)
            
            data.to_csv(caminho_saida, index=False, sep=";", encoding="utf-8")
            print(f" [OK] Arquivo salvo em: {caminho_saida}\n")

        except Exception as e:
            print(f" [ERRO] Falha ao processar o arquivo {arquivo}: {e}\n")

# Execução Principal
if __name__ == "__main__":
    arquivos_para_processar = get_data()
    pre_process(arquivos_para_processar)