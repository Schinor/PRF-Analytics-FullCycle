# Sobre o projeto

Este projeto é uma base para testes e fixação de aprendizado/estudo de alguns bootcamps que participei. Ele foi pensado para rodar todo o ciclo de uma ETL até a sua disponibilização/consumo, seja para modelos de aprendizado ou para análises de dados. A principio o projeto surgiu como base para escrita de um artigo cientifico sobre acidentes de transito no Brasil, mas acabou que não foi para frente, depois do fracasso do artigo decidi seguir ocmo uma base de fixação de conhecimento. Por fim, o projeto também segue alguns padrões cientificos em algumas decisões, como ele seria utilizado para gerar uma rtigfo pópsterioremente, cerneei todas minhas decisões em pautas justificaveis e que pudessem ser defendidas, sem achismos ou pressupostos.

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
