# Observatório — acervo político documentado

Site responsivo com HTML, CSS e JavaScript, gerado e servido por Python 3 (somente biblioteca padrão).

## Executar

Dentro desta pasta:

```sh
python3 app.py --port 8000
```

Abra http://127.0.0.1:8000. O servidor escuta somente na máquina local. `GET /api/cases` retorna o acervo JSON.

Para gerar a versão estática sem iniciar servidor:

```sh
python3 build.py
```

`dist/index.html` também funciona diretamente no navegador. Os gráficos usam JavaScript sem bibliotecas externas. As fontes Google são opcionais, com fontes alternativas locais.

## Arquivos

- `app.py`: servidor local Python e endpoint do acervo.
- `build.py`: valida campos essenciais e gera HTML e JSON publicados.
- `cases.json`: conteúdo editorial; cada episódio tem pessoas, tema, ano de referência, último marco documentado, situação, contexto e fontes.
- `template.html`: estrutura da página e ponto de inclusão dos dados.
- `dist/style.css`: identidade visual e regras responsivas.
- `dist/app.js`: gráficos, filtros, perfis, fichas, método e interface opcional WebMCP.
- `dist/images`: três fotografias conjuntas oficiais, com créditos e licenças nos perfis.

## Escopo editorial

21 episódios selecionados, seis aliados, seis temas. Consulta editorial em 09/10/2026. O acervo não é exaustivo nem atualizado automaticamente. Cada ficha informa a data da fonte mais recente reunida. As contagens são de episódios, não de crimes; há sobreposição temática e processual. Pessoas que aparecem como julgadoras não são automaticamente tratadas como acusadas. O vínculo político não transfere responsabilidade por conduta alheia.

Fotos: Alan Santos/PR, Marcos Corrêa/PR e Carolina Antunes/PR, via Wikimedia Commons, CC BY 2.0. O site contém links para originais, licença e aviso de recorte de exibição.

## Publicação

A versão Sites publica os arquivos estáticos gerados por Python. O serviço hospedado não executa o servidor Python; para execução Python use `app.py` localmente ou em hospedagem compatível. Não há login próprio, banco de dados ou coleta de dados dos visitantes implementados pelo projeto.

## Atualizar

Edite `cases.json`, acrescente fontes verificáveis e ajuste as datas. Execute `python3 build.py`. Não substitua uma situação processual por inferência de manchete; mantenha arquivamentos, rejeições, defesas e limites das decisões. Depois de alterar arquivos estáticos, recarregue a prévia.

## Falas na mídia

A nova aba contém 23 declarações de 15 figuras públicas: seis integrantes da família Bolsonaro e nove aliados ou integrantes históricos do governo. São registros selecionados de 2014 a 2025, sem pretensão de esgotar todas as falas. Os 21 episódios do acervo anterior permanecem separados dessa contagem.

- `statements.json`: trechos literais curtos, sínteses identificadas, autor, veículo, contexto, resposta, datas e fontes.
- `GET /api/statements`: endpoint Python para as declarações.
- As datas distinguem fala, gravação e divulgação; quando a fonte não permite precisão diária, usa-se apenas o mês.
- As aspas reproduzem trechos curtos. Uma ficha sem citação é marcada como síntese editorial.
- Gráficos e busca da aba operam apenas sobre as declarações. Explicações, pedidos de desculpas e desdobramentos judiciais ficam visíveis nas fichas.

## Documentos e leitura crítica

A edição documental acrescenta análise editorial identificada nas 21 fichas, cronologias de Flávio e da AP 2668, biblioteca filtrável e atalhos para páginas verificadas. A seleção não é exaustiva.

- `documents.json`: metadados, origem, alcance, vínculos, páginas, tamanho e SHA-256.
- `dist/documents/`: acórdão AP 2668 (1.991 páginas), denúncia PGR (272) e notas da Câmara (331).
- `originais/relatorio-pf-golpe.pdf`: relatório integral PF (884 páginas), preservado no projeto. Na versão hospedada, este arquivo grande abre no endereço oficial do STF.
- Relatório CPI: link para o documento e para a página da comissão. O portal do Senado bloqueou o download automatizado; não há cópia local nem verificação integral desse PDF.

Os quatro PDFs copiados somam 3.478 páginas e foram preservados sem edição. A conferência verificou abertura, identificação e páginas do roteiro de leitura, não todas as afirmações de cada documento. O hash identifica os bytes baixados; assinaturas digitais não foram auditadas criptograficamente. As páginas dos atalhos são posições no PDF. A íntegra de um processo pode incluir dados pessoais; a interface não reproduz CPFs ou endereços residenciais.

As análises editoriais são interpretações críticas das fontes de cada ficha. Denúncias e relatórios policiais não têm o mesmo valor processual de acórdãos; as decisões posteriores e os argumentos da defesa devem ser considerados. Nem todos os episódios têm documentos integrais incorporados.

## Componentes adicionais

- `lula_policies.json`: catálogo documental de políticas públicas.
- `golpe-de-estado.html`: página temática; `pages.py` gera páginas permanentes.
- `visitor_counter.py`: contador agregado com SQLite, implantado como serviço separado na VPS; veja `COUNTER.md`. O servidor local não inicia esse serviço automaticamente.
- `dist/layout-fixes.css`: ajustes de contraste e responsividade.
- `dist/site-counter.js`: barra de contagem e alinhamento do menu lateral.
- `automation/README.md`: coleta, revisão e publicação editorial.

A pasta `dist/` contém os recursos estáticos e documentos locais necessários à interface. Credenciais, configurações locais de ferramentas, banco de visitantes e backups não fazem parte do repositório. Publicar o código no GitHub não altera a hospedagem da VPS.
