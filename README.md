
Estrutura do projeto:

    prf-analytics-fullcycle/
    ├── .github/workflows/   # (CI/CD) Automação via GitHub Actions
    ├── data/                # (Local) Onde os CSVs brutos e processados ficam temporariamente
    ├── docker/              # Arquivos de configuração de containers (MySQL, Airflow/Prefect)
    ├── etl/                 # O Coração do projeto
    │   ├── extract.py       # Crawler que baixa o CSV
    │   ├── transform.py     # Limpeza com Pandas
    │   └── load.py          # Salva no Banco de Dados
    ├── api/                 # Backend (FastAPI)
    ├── dashboard/           # Frontend (Angular ou Streamlit)
    ├── requirements.txt     # Dependências
    ├── docker-compose.yml   # Sobe o banco e a API com um comando
    └── README.md            # Documentação
