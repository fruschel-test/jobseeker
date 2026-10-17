# Talent Bridge AU/NZ — agente de vagas

Agente estático executado três vezes por dia via GitHub Actions. Pesquisa resultados da Brave Search API e publica um relatório no GitHub Pages. Sem banco de dados; sem scraping direto de SEEK, LinkedIn ou Indeed.

## Dependências

- Chave da **Brave Search API** e plano aplicável. Confira preços/limites: https://brave.com/search/api/
- Para envio automático por e-mail, conta Resend e domínio/endereço de remetente verificado: https://resend.com/

## Configuração

Em GitHub → **Settings → Secrets and variables → Actions**, configure os seguintes repository secrets:

1. `BRAVE_SEARCH_API_KEY`: chave da Brave Search API.
2. `RESEND_API_KEY`: chave de API do Resend.
3. `EMAIL_FROM`: remetente autorizado/verificado no Resend, por exemplo `Talent Bridge <jobs@seu-dominio-verificado.com>`.

Após configurar, abra **Actions → Refresh job report → Run workflow** para testar. Cada execução agenda/publica o dashboard e tenta enviar um e-mail para **fabio@e-ruschel.com** com os contadores, links e até 12 vagas em destaque. Se os secrets de e-mail não estiverem configurados, a publicação continua, mas o e-mail é ignorado e isso aparece nos logs. Se o envio falhar, a etapa registra o erro sem desfazer a publicação.

Em **Settings → Pages**, selecione **GitHub Actions** como fonte de publicação e confirme que Actions está habilitado em **Settings → Actions → General**.

## Frequência

`0 7,11,23 * * *` = 07:00, 11:00 e 23:00 UTC, equivalentes a 04:00, 08:00 e 20:00 no horário de Brasília (UTC-3). O GitHub Actions pode atrasar execuções agendadas em períodos de alta demanda.

## Segurança e limitações

- Nunca coloque chaves API no HTML ou em arquivos versionados; use GitHub Actions Secrets.
- O relatório é público se o site/repositório for público.
- O script consulta somente a API de pesquisa e usa título, URL e snippet devolvidos por ela. Não baixa nem analisa diretamente as páginas dos portais.
- O filtro exclui vagas que mencionam trabalho remoto e exige sinais de localização no próprio resultado ou domínio local; isso reduz falsos positivos, mas pode deixar de fora anúncios legítimos com poucos detalhes no snippet.
- A classificação é heurística; “menção encontrada” não garante sponsorship nem que a vaga siga aberta. Confirme no anúncio original se aceita candidatos offshore.
- Não há banco de dados nem histórico persistente. Cada execução substitui o relatório anterior.
- A busca depende do índice externo e não garante cobertura total ou atualização imediata.

## Cobertura de fontes

O agente realiza buscas web indexadas pela Brave Search API com consultas direcionadas para fontes como SEEK, Indeed, LinkedIn Jobs, Jora, Trade Me Jobs e páginas de carreiras que usam Greenhouse, Lever, Ashby ou SmartRecruiters, além de buscas gerais e sites de empregadores. Ele não faz scraping direto dessas plataformas; a disponibilidade depende do que o mecanismo de busca indexa.

A versão ampliada usa 16 consultas por execução (48 por dia no agendamento normal). Verifique a cota do plano da Brave antes de usar; não presuma que a API seja gratuita ou ilimitada. Os filtros de localização, sponsorship e relocation são heurísticos e dependem dos resultados de busca.
