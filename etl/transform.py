# Importações
from dotenv import load_dotenv
import pandas as pd
import openpyxl
import os

load_dotenv()

# Importando os caminhos

BASE_PATH = os.getenv("BASE_PATH")
RAW_DATA_PATH = os.path.join(BASE_PATH, os.getenv("RAW_DATA_PATH"))
PROCESSED_DATA_PATH = os.path.join(BASE_PATH, os.getenv("PROCESSED_DATA_PATH"))


# Funções


def get_data():
    arquivos = os.listdir(RAW_DATA_PATH)
    return arquivos

# 1 - Etapa do pré-processamento
def pre_process(arquivos: list[str]):
    try:
        if not arquivos:
            print("Nenhum arquivo econtrado")
        for arquivo in arquivos:
            data = pd.read_csv(os.path.join(RAW_DATA_PATH, arquivo), 
                            header=0, 
                            sep=";", 
                            encoding="latin1", 
                            dtype={5: str, 6: str})
            
    except Exception as e:
        if not arquivos:
            print("Nenhum arquivo econtrado")
        for arquivo in arquivos:
            data = pd.read_excel(os.path.join(RAW_DATA_PATH, arquivo), 
                            header=0, 
                            sep=";", 
                            encoding="latin1", 
                            dtype={5: str, 6: str})
    return data

if __name__ == "__main__":
    preprocessamento()