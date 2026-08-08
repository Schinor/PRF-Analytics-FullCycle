from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import text
import os
from api.database import engine

load_dotenv()

BASE_PATH = os.getenv("BASE_PATH")
PROCESSED_PATH = os.path.join(BASE_PATH, os.getenv("PROCESSED_DATA_PATH"))

# Tabelas de apoio (lookup): nome da tabela -> (coluna UNIQUE no banco, coluna correspondente no CSV)
LOOKUP_TABLES = {
    "UF": ("sigla", "uf"),
    "BR": ("numero", "br"),
    "Regional": ("sigla", "regional"),
    "Delegacia": ("sigla", "delegacia"),
    "UOP": ("sigla", "uop"),
}

# Colunas finais da tabela fato, na ordem/nomes exatos do banco (sem "id": é gerado pelo Postgres)
FACT_COLUMNS = [
    "data_inversa", "dia_semana", "horario", "uf_id", "br_id", "km",
    "municipio", "latitude", "longitude", "causa_acidente", "tipo_acidente",
    "classificacao_acidente", "fase_dia", "sentido_via", "condicao_metereologica",
    "tipo_pista", "tracado_via", "uso_solo", "pessoas", "mortos", "feridos_leves",
    "feridos_graves", "ilesos", "ignorados", "feridos", "veiculos",
    "regional_id", "delegacia_id", "uop_id", "is_fimdesemana",
]

# Colunas NOT NULL na tabela fato: se vierem vazias, a linha precisa ser descartada
COLUNAS_OBRIGATORIAS = ["uf_id", "br_id", "is_fimdesemana"]


def listar_arquivos():
    """Retorna os caminhos completos de todos os arquivos na pasta de dados processados."""
    nomes = os.listdir(PROCESSED_PATH)
    return [os.path.join(PROCESSED_PATH, nome) for nome in nomes]


def ler_arquivo(caminho):
    """Lê um CSV ou Excel processado. Detecta o tipo pela extensão."""
    if caminho.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(caminho)
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig")


def normalizar_texto(serie):
    """
    Converte uma coluna para texto de forma estável, resolvendo o problema de
    valores numéricos que às vezes chegam como float (381.0) e às vezes como
    int/str (381) dependendo do arquivo/ano. Sem isso, "381.0" e "381" virariam
    dois registros diferentes nas tabelas de apoio.
    """
    def limpar(v):
        if pd.isna(v):
            return None
        if isinstance(v, float) and v.is_integer():
            v = int(v)
        texto = str(v).strip()
        return texto if texto else None
    return serie.map(limpar)


def already_loaded(nome_arquivo, conexao):
    """Verifica na tabela de controle se este arquivo já foi carregado antes."""
    resultado = conexao.execute(
        text('SELECT 1 FROM "Arquivo_Carregado" WHERE nome_arquivo = :nome'),
        {"nome": nome_arquivo},
    ).fetchone()
    return resultado is not None


def marcar_carregado(nome_arquivo, conexao):
    conexao.execute(
        text('INSERT INTO "Arquivo_Carregado" (nome_arquivo) VALUES (:nome)'),
        {"nome": nome_arquivo},
    )


def upsert_lookup(df, tabela, coluna_unica, coluna_df, conexao):
    """
    Garante que todo valor distinto e normalizado de `coluna_df` exista na
    tabela de apoio `tabela` e devolve um dicionário {valor_texto: id}.
    """
    if coluna_df not in df.columns:
        return {}

    valores = normalizar_texto(df[coluna_df]).dropna().unique().tolist()
    if not valores:
        return {}

    conexao.execute(
        text(f'INSERT INTO "{tabela}" ({coluna_unica}) VALUES (:valor) '
             f'ON CONFLICT ({coluna_unica}) DO NOTHING'),
        [{"valor": v} for v in valores],
    )
    resultado = conexao.execute(
        text(f'SELECT id, {coluna_unica} FROM "{tabela}" WHERE {coluna_unica} = ANY(:valores)'),
        {"valores": valores},
    )
    return {linha[1]: linha[0] for linha in resultado}


def montar_tabela_fato(df, mapas):
    """
    Troca as colunas de texto (uf, br, regional, delegacia, uop) pelos ids
    correspondentes, ajusta tipos e seleciona só as colunas da tabela fato.
    """
    df = df.copy()

    df["uf_id"] = normalizar_texto(df["uf"]).map(mapas.get("UF", {}))
    df["br_id"] = normalizar_texto(df["br"]).map(mapas.get("BR", {}))
    df["regional_id"] = normalizar_texto(df["regional"]).map(mapas.get("Regional", {})) \
        if "regional" in df.columns else None
    df["delegacia_id"] = normalizar_texto(df["delegacia"]).map(mapas.get("Delegacia", {})) \
        if "delegacia" in df.columns else None
    df["uop_id"] = normalizar_texto(df["uop"]).map(mapas.get("UOP", {})) \
        if "uop" in df.columns else None

    if "fim_de_semana" in df.columns:
        df = df.rename(columns={"fim_de_semana": "is_fimdesemana"})
    # fim_de_semana chega como 0/1 (int); a coluna no banco é BOOLEAN e o
    # Postgres não converte integer -> boolean implicitamente.
    df["is_fimdesemana"] = df["is_fimdesemana"].astype(bool)

    faltando = df[COLUNAS_OBRIGATORIAS].isna().any(axis=1)
    if faltando.any():
        print(f"  Aviso: {faltando.sum()} linha(s) descartada(s) por uf/br/fim_de_semana ausentes")
        df = df[~faltando]

    colunas_presentes = [c for c in FACT_COLUMNS if c in df.columns]
    return df[colunas_presentes]


def processar_arquivo(caminho, engine):
    nome_arquivo = os.path.basename(caminho)

    with engine.begin() as conexao:
        if already_loaded(nome_arquivo, conexao):
            print(f"  {nome_arquivo} já foi carregado antes, pulando.")
            return

        df = ler_arquivo(caminho)

        mapas = {
            tabela: upsert_lookup(df, tabela, coluna_unica, coluna_df, conexao)
            for tabela, (coluna_unica, coluna_df) in LOOKUP_TABLES.items()
        }

        df_fato = montar_tabela_fato(df, mapas)
        if not df_fato.empty:
            df_fato.to_sql("Acidentes_Registrados", con=conexao, if_exists="append", index=False)

        marcar_carregado(nome_arquivo, conexao)
        # tudo dentro do "with engine.begin()": se algo falhar aqui, TUDO é
        # desfeito (nem lookups, nem fato, nem o marcador de "carregado" ficam salvos)
        print(f"  {len(df_fato)} registros inseridos de {nome_arquivo}")


def main(engine):
    for caminho in listar_arquivos():
        print(f"Processando {caminho}...")
        processar_arquivo(caminho, engine)
    print("Carga finalizada.")


if __name__ == "__main__":
    main(engine)