# ==============================================================================
# PRF Analytics — Etapa de Pré-processamento
# Autor: Schinor | Versão corrigida
# ==============================================================================

from dotenv import load_dotenv
import pandas as pd
import numpy as np
import chardet
import os
import re

load_dotenv()

BASE_PATH         = os.getenv("BASE_PATH")
RAW_DATA_PATH     = os.path.join(BASE_PATH, os.getenv("RAW_DATA_PATH"))
PROCESSED_DATA_PATH = os.path.join(BASE_PATH, os.getenv("PROCESSED_DATA_PATH"))


# ------------------------------------------------------------------------------
# UTILITÁRIO: Detecta o encoding real do arquivo via chardet
# Por que: lógica manual de Mojibake é frágil e cobre apenas um cenário.
# O chardet lê os bytes brutos e retorna o encoding com um score de confiança.
# ------------------------------------------------------------------------------
def detect_encoding(filepath: str) -> str:
    with open(filepath, "rb") as f:
        # Lê até 100KB — suficiente para uma detecção confiável sem carregar tudo
        raw = f.read(100_000)
    result = chardet.detect(raw)
    encoding = result.get("encoding") or "utf-8"
    confidence = result.get("confidence", 0)
    print(f"   Encoding detectado: {encoding} (confiança: {confidence:.0%})")
    # Normaliza aliases comuns que o pandas não aceita diretamente
    if encoding.upper() in ("ISO-8859-1", "WINDOWS-1252", "CP1252"):
        return "latin1"
    return encoding


# ------------------------------------------------------------------------------
# UTILITÁRIO: Parse de data com múltiplos formatos e log de falhas
# Por que: arquivos de anos diferentes usam formatos distintos.
# O errors='coerce' silencia falhas — precisamos saber quantas datas quebraram.
# ------------------------------------------------------------------------------
def parse_data_inversa(series: pd.Series, ano_arquivo: int) -> pd.Series:
    # Formatos mais comuns nos dados da PRF, em ordem de prioridade
    formatos = ["%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"]
    
    resultado = pd.Series(pd.NaT, index=series.index)
    restante = series.copy()

    for fmt in formatos:
        parsed = pd.to_datetime(restante, format=fmt, errors="coerce")
        acertou = parsed.notna()
        resultado[acertou] = parsed[acertou]
        restante = restante[~acertou & restante.notna()]
        if restante.empty:
            break

    falhas = resultado.isna().sum()
    total = series.notna().sum()
    if falhas > 0:
        print(f"   ⚠ data_inversa: {falhas}/{total} datas não parseadas (ano {ano_arquivo})")
        print(f"     Exemplos de falha: {series[resultado.isna()].dropna().head(3).tolist()}")
    else:
        print(f"   ✓ data_inversa: todas as {total} datas parseadas com sucesso")

    return resultado


# ------------------------------------------------------------------------------
# COLETA: Lista arquivos CSV no diretório raw
# ------------------------------------------------------------------------------
def get_data() -> list[str]:
    if not os.path.exists(RAW_DATA_PATH):
        print(f"[ERRO] Diretório não encontrado: {RAW_DATA_PATH}")
        return []
    arquivos = [f for f in os.listdir(RAW_DATA_PATH) if f.endswith(".csv")]
    print(f"[INFO] {len(arquivos)} arquivo(s) encontrado(s) para processamento.")
    return arquivos


# ------------------------------------------------------------------------------
# PRÉ-PROCESSAMENTO PRINCIPAL
# ------------------------------------------------------------------------------
def pre_process(arquivos: list[str]):
    if not arquivos:
        print("Nenhum arquivo encontrado.")
        return

    for arquivo in arquivos:
        print(f"\n{'='*60}")
        print(f" Processando: {arquivo}")
        print(f"{'='*60}")
        caminho_completo = os.path.join(RAW_DATA_PATH, arquivo)

        try:
            # Extrai o ano do nome do arquivo
            match = re.search(r"(\d{4})", arquivo)
            ano_arquivo = int(match.group(1)) if match else 2000
            print(f"   Ano inferido: {ano_arquivo}")

            # ------------------------------------------------------------------
            # ETAPA 1 — Leitura com encoding detectado automaticamente
            # Correção do problema principal: ao invés de adivinhar com try/except,
            # detectamos o encoding real dos bytes antes de qualquer leitura.
            # O dtype=str para todas as colunas na leitura garante que nenhuma
            # conversão automática do pandas corrumpa os dados antes do nosso
            # tratamento explícito abaixo.
            # ------------------------------------------------------------------
            encoding_detectado = detect_encoding(caminho_completo)

            data = pd.read_csv(
                caminho_completo,
                header=0,
                sep=";",
                encoding=encoding_detectado,
                dtype=str,          # Lê tudo como string — convertemos nós mesmos
                low_memory=False,   # Evita o DtypeWarning de inferência de tipo misto
                keep_default_na=False  # Não converte "N/A", "(null)" automaticamente ainda
            )
            print(f"   Linhas lidas: {len(data):,} | Colunas: {len(data.columns)}")

            # ------------------------------------------------------------------
            # ETAPA 2 — Limpeza geral
            # ------------------------------------------------------------------

            # Remove coluna id (surrogate key sem valor analítico)
            if "id" in data.columns:
                data = data.drop(columns=["id"])

            # Normaliza todos os marcadores de nulo para NaN real do pandas
            # Feito ANTES de qualquer conversão de tipo
            nulos_textuais = ["(null)", "N/A", "NA", "", " ", "nan", "NaN"]
            data.replace(nulos_textuais, np.nan, inplace=True)

            # ------------------------------------------------------------------
            # ETAPA 3 — Conversões explícitas por coluna
            # Cada conversão tem um motivo claro.
            # ------------------------------------------------------------------

            # Colunas categóricas: string do pandas (nullable) é mais eficiente
            # que object para colunas com cardinalidade baixa
            colunas_string = [
                "uf", "municipio", "causa_acidente", "tipo_acidente",
                "classificacao_acidente", "fase_dia", "sentido_via",
                "condicao_metereologica", "tipo_pista", "tracado_via", "uso_solo"
            ]
            for col in colunas_string:
                if col in data.columns:
                    # strip() remove espaços extras que aparecem em alguns arquivos
                    data[col] = data[col].str.strip().astype("string")

            # br: pode ser número ou "S/N" em alguns anos — mantemos como string
            if "br" in data.columns:
                data["br"] = data["br"].str.strip().astype("string")

            # km: vírgula decimal é padrão brasileiro no CSV da PRF
            if "km" in data.columns:
                data["km"] = pd.to_numeric(
                    data["km"].str.replace(",", ".", regex=False),
                    errors="coerce"
                )

            # data_inversa: usa nossa função robusta com múltiplos formatos
            if "data_inversa" in data.columns:
                data["data_inversa"] = parse_data_inversa(data["data_inversa"], ano_arquivo)

            # horario: extrai apenas o time, descartando a parte de data
            if "horario" in data.columns:
                data["horario"] = pd.to_datetime(
                    data["horario"], format="%H:%M:%S", errors="coerce"
                ).dt.time

            # dia_semana: categoria com feature de fim de semana derivada
            if "dia_semana" in data.columns:
                data["dia_semana"] = data["dia_semana"].astype("category")
                finais_de_semana = {
                    "sábado", "sabado", "Sábado", "Sabado", "SÁBADO", "SABADO",
                    "domingo", "Domingo", "DOMINGO"
                }
                data["fim_de_semana"] = data["dia_semana"].isin(finais_de_semana).astype(int)

            # Colunas numéricas inteiras (contagens)
            colunas_int = ["pessoas", "mortos", "feridos_leves", "feridos_graves",
                           "ilesos", "ignorados", "feridos", "veiculos", "ano"]
            for col in colunas_int:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors="coerce").astype("Int64")

            # ------------------------------------------------------------------
            # ETAPA 4 — Tratamento condicional por ano (estrutura do schema)
            # Arquivos >= 2017 têm latitude/longitude e colunas operacionais
            # ------------------------------------------------------------------
            if ano_arquivo >= 2017:
                print(f"   Schema novo (>= 2017): processando lat/lon e colunas operacionais")

                for col in ["delegacia", "uop", "regional"]:
                    if col in data.columns:
                        data[col] = data[col].replace(nulos_textuais, np.nan)
                        data[col] = data[col].astype("string")

                if "latitude" in data.columns and "longitude" in data.columns:
                    data["latitude"] = pd.to_numeric(
                        data["latitude"].str.replace(",", ".", regex=False), errors="coerce"
                    )
                    data["longitude"] = pd.to_numeric(
                        data["longitude"].str.replace(",", ".", regex=False), errors="coerce"
                    )

                    antes = len(data)
                    # Remove registros com coordenadas ausentes ou fora dos limites do Brasil
                    # Bbox aproximado: lat [-34, 6], lon [-74, -28]
                    data = data.dropna(subset=["latitude", "longitude"])
                    data = data[
                        (data["latitude"].between(-34, 6)) &
                        (data["longitude"].between(-74, -28))
                    ]
                    removidos = antes - len(data)
                    if removidos > 0:
                        print(f"   ⚠ {removidos} registros removidos por coordenadas inválidas")

            else:
                print(f"   Schema antigo (< 2017): preenchendo colunas ausentes com NA")
                for col in ["latitude", "longitude", "regional", "delegacia", "uop"]:
                    data[col] = pd.NA

            # ------------------------------------------------------------------
            # ETAPA 5 — Salvamento
            # Encoding UTF-8 com BOM (utf-8-sig) para compatibilidade com Excel,
            # que ignora BOM mas lê os acentos corretamente.
            # ------------------------------------------------------------------
            arquivo_saida = f"processed_{arquivo}"
            caminho_saida = os.path.join(PROCESSED_DATA_PATH, arquivo_saida)
            os.makedirs(PROCESSED_DATA_PATH, exist_ok=True)

            data.to_csv(
                caminho_saida,
                index=False,
                sep=";",
                encoding="utf-8-sig"   # UTF-8 com BOM — acentos preservados em qualquer leitor
            )

            print(f"\n   [OK] Salvo em: {caminho_saida}")
            print(f"   Linhas finais: {len(data):,}")

        except Exception as e:
            print(f"\n   [ERRO] Falha ao processar {arquivo}: {e}\n")
            raise  # Re-raise para não engolir erros silenciosamente em dev


# ------------------------------------------------------------------------------
# EXECUÇÃO
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    arquivos = get_data()
    pre_process(arquivos)