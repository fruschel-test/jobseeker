# Talent Bridge AU/NZ — agente de vagas

Agente estático executado três vezes por dia via GitHub Actions. Pesquisa resultados da Brave Search API e publica um relatório no GitHub Pages. Sem banco de dados; sem scraping direto de SEEK, LinkedIn ou Indeed.

## Dependência
É necessária uma chave da **Brave Search API** e um plano aplicável. Confira os preços/limites atuais antes de ativar: https://brave.com/search/api/

## Configuração
1. Envie todos os arquivos do pacote para a raiz do repositório `talent-bridge-au-nz` na branch `main`.
2. Em GitHub → **Settings → Secrets and variables → Actions → New repository secret**, crie `BRAVE_SEARCH_API_KEY` com sua chave da Brave.
3. Em **Settings → Pages**, selecione **GitHub Actions** como fonte de publicação.
4. Confirme que GitHub Actions está habilitado em **Settings → Actions → General**.
5. Abra **Actions → Refresh job report → Run workflow** para testar.
6. O workflow publica o relatório no GitHub Pages; use o URL mostrado no job de deployment.

## Frequência
`0 7,11,23 * * *` = 07:00, 11:00 e 23:00 UTC, equivalentes a 04:00, 08:00 e 20:00 no horário de Brasília (UTC-3). O GitHub Actions pode atrasar execuções agendadas em períodos de alta demanda.

## Segurança e limitações
- Nunca coloque a chave API no HTML ou em arquivos versionados; use o GitHub Actions Secret.
- O relatório é público se o site/repositório for público.
- O script consulta somente a API de pesquisa e usa título, URL e snippet devolvidos por ela. Não baixa nem analisa diretamente as páginas dos portais.
- O filtro exclui vagas que mencionam trabalho remoto e exige sinais de localização no próprio resultado ou domínio local; isso reduz falsos positivos, mas pode deixar de fora anúncios legítimos com poucos detalhes no snippet.
- A classificação é heurística; “menção encontrada” não garante sponsorship nem que a vaga siga aberta. Confirme no anúncio original se aceita candidatos offshore.
- Não há banco de dados nem histórico persistente. Cada execução substitui o relatório anterior.
- A busca depende do índice externo e não garante cobertura total ou atualização imediata.


## Cobertura ampliada de fontes

O agente realiza buscas web indexadas pela Brave Search API com consultas direcionadas para diferentes fontes, incluindo SEEK, Indeed, LinkedIn Jobs, Jora, Trade Me Jobs e páginas de carreiras que usam Greenhouse, Lever, Ashby ou SmartRecruiters, além de buscas gerais e sites de empregadores. Ele não faz scraping direto dessas plataformas; a disponibilidade depende do que o mecanismo de busca indexa.

A versão ampliada usa 16 consultas por execução (32 por dia no agendamento normal). Verifique o limite/cota do plano da Brave antes de usar; não presuma que a API seja gratuita ou ilimitada. O código continua sem banco de dados e o relatório anterior é substituído a cada execução.

Os filtros continuam heurísticos: a localização e a evidência de sponsorship/relocation são avaliadas a partir dos resultados de busca, não de uma verificação automática integral de cada anúncio. Abra a fonte original para confirmar elegibilidade offshore, modalidade presencial/híbrida e condições de visto.
