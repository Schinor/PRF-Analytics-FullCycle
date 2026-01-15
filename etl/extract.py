import asyncio
import os
import zipfile
import re  # Importamos Regex para extrair o ano com precisão
from playwright.async_api import async_playwright

# --- FUNÇÃO AUXILIAR: Extração ---
def extrair_arquivo_zip(caminho_zip, pasta_destino):
    try:
        if zipfile.is_zipfile(caminho_zip):
            print(f"   [!] Extraindo conteúdo do ZIP...")
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_destino)
            print(f"   [ok] Arquivos extraídos em: {pasta_destino}")
            os.remove(caminho_zip)
        else:
            print("   [erro] O arquivo baixado não é um ZIP válido.")
    except Exception as e:
        print(f"   [erro] Falha ao extrair: {e}")

async def main():
    async with async_playwright() as p:
        # --- 1. CONFIGURAÇÃO DE PASTAS ---
        diretorio_script = os.path.dirname(os.path.abspath(__file__))
        diretorio_raiz = os.path.dirname(diretorio_script)
        pasta_destino = os.path.join(diretorio_raiz, "data")
        
        os.makedirs(pasta_destino, exist_ok=True)
        print(f"Diretório de verificação/saída: {pasta_destino}")

        # --- 2. INICIALIZAÇÃO DO NAVEGADOR ---
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("Acessando a página da PRF...")
        await page.goto("https://www.gov.br/prf/pt-br/acesso-a-informacao/dados-abertos/dados-abertos-da-prf", timeout=60000)

        # Limpeza Visual
        await page.evaluate("""
            const header = document.querySelector('header');
            if (header) header.style.display = 'none';
            const barra = document.querySelector('barra-govbr');
            if (barra) barra.style.display = 'none';
        """)

        try:
            btn_acidentes = page.get_by_text("Acidentes de Trânsito", exact=False)
            if await btn_acidentes.is_visible():
                await btn_acidentes.click()
        except:
            pass 

        print("Mapeando arquivos...")
        linhas = page.locator("tbody tr")
        total_linhas = await linhas.count()
        
        # --- 3. LOOP COM VERIFICAÇÃO DE DUPLICIDADE ---
        for i in range(total_linhas):
            linha_atual = linhas.nth(i)
            texto_linha = await linha_atual.inner_text()

            if "Agrupados por ocorrência" in texto_linha:
                
                # --- PASSO A: Identificar o nome ANTES de baixar ---
                # Usamos Regex para achar 4 dígitos seguidos (o ano)
                match_ano = re.search(r'\d{4}', texto_linha)
                if match_ano:
                    ano_str = match_ano.group(0)
                else:
                    ano_str = "desconhecido"
                
                # Definimos o nome padrão que queremos
                nome_padrao_zip = f"datatran_{ano_str}_ocorrencia.zip"
                caminho_completo_zip = os.path.join(pasta_destino, nome_padrao_zip)

                # --- PASSO B: A Verificação (O Guardião) ---
                if os.path.exists(caminho_completo_zip):
                    print(f"Ignorando {ano_str}: Arquivo já existe em '{nome_padrao_zip}'.")
                    continue  # <--- Isso faz pular para o próximo 'i' do loop
                
                # Se chegou aqui, é porque o arquivo NÃO existe. Vamos baixar.
                print(f"\n--- Baixando dados de {ano_str} ---")
                
                botao_prf = linha_atual.locator("a").first

                try:
                    async with context.expect_page() as nova_pagina_info:
                        await botao_prf.click(force=True)
                    
                    pagina_drive = await nova_pagina_info.value
                    await pagina_drive.wait_for_load_state()
                    
                    btn_download_drive = pagina_drive.locator('[aria-label="Baixar"]')
                    await btn_download_drive.wait_for(state="visible", timeout=15000)

                    async with pagina_drive.expect_download(timeout=60000) as download_info:
                        await btn_download_drive.click()

                    download = await download_info.value
                    
                    # --- PASSO C: Salvar com o nome padronizado ---
                    # Não usamos mais o suggested_filename, forçamos o nosso nome padrão
                    await download.save_as(caminho_completo_zip)
                    print(f"Download salvo: {nome_padrao_zip}")

                    # Extração
                    extrair_arquivo_zip(caminho_completo_zip, pasta_destino)

                    await pagina_drive.close()
                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"Erro na linha {i}: {e}")
                    try:
                        if 'pagina_drive' in locals():
                            await pagina_drive.close()
                    except:
                        pass

        print("\nProcesso Finalizado!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())