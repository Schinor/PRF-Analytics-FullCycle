# Usa uma imagem leve do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Variáveis de ambiente para o Python não gerar arquivos .pyc e logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependências do sistema necessárias para compilar algumas libs (opcional, mas bom ter)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da API para dentro do container
COPY . .

# Comando para rodar a API (Uvicorn)
# --host 0.0.0.0 é OBRIGATÓRIO no Docker (libera acesso externo)
# --reload permite que você altere o código e o servidor reinicie sozinho
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]