# Observatório — acervo político documentado

Projeto em Python 3, HTML, CSS e JavaScript, com gráficos interativos, fichas, fontes documentais e páginas permanentes.

Site hospedado: https://observatorio.lula.com.vc/

## Executar localmente

Requer Python 3. O núcleo usa somente a biblioteca padrão.

```sh
python3 app.py --port 8000
```

Abra http://127.0.0.1:8000/. Sirva os arquivos por HTTP: abrir o HTML diretamente como arquivo não oferece suporte às requisições da interface.

## Gerar e verificar

```sh
python3 build.py
python3 verify.py
```

A versão gerada fica em `dist/`. A verificação confere referências locais, vínculos documentais e hashes dos PDFs incorporados.

## Organização

- `cases.json`, `statements.json` e `lula_records.json`: fontes editoriais do acervo.
- `lula_policies.json`: catálogo documental de políticas públicas.
- `documents.json`: metadados, origem, páginas e hashes dos documentos.
- `template.html`, `build.py` e `pages.py`: geração das páginas.
- `golpe-de-estado.html`: fonte da página temática.
- `dist/`: HTML gerado, CSS, JavaScript, imagens e documentos locais.
- `dist/layout-fixes.css`: ajustes de contraste e responsividade.
- `visitor_counter.py`: serviço separado de contagem, com SQLite; consulte [COUNTER.md](COUNTER.md).
- `automation/`: coleta e revisão editorial; consulte [automation/README.md](automation/README.md).

Esta cópia gera 47 fichas de episódios e medidas, 29 falas e um catálogo independente de 37 medidas legais. São formatos distintos e podem conter sobreposição; não some as contagens como número de crimes, pessoas ou realizações únicas. A seleção não é exaustiva. Cada registro deve ser consultado junto com suas fontes e datas.

## Serviços e publicação

O servidor local oferece `/api/cases` e `/api/statements`. O contador de visitantes requer seu próprio serviço e proxy para `/api/site-counter`; não é iniciado automaticamente por `app.py`. O diretório SQLite de produção deve ficar fora da pasta pública.

O coletor cria candidatos para revisão editorial; coleta não equivale a publicação automática. Configure usuários, diretórios e unidades de serviço conforme o ambiente antes de ativar a automação.

Publicar este repositório não altera a hospedagem na VPS. Esta cópia foi preparada a partir do projeto local; arquivos e configurações existentes apenas no servidor de produção não são automaticamente sincronizados.

## Fontes e atribuições

O acervo diferencia acusações, condenações, anulações, arquivamentos e opinião editorial. Parentesco ou associação política não transfere responsabilidade criminal. Confira sempre o documento e a data de cada situação processual.

As imagens oficiais incorporadas têm créditos e referências nos perfis. Os documentos públicos preservam suas fontes e metadados em `documents.json`; o hash verifica os bytes da cópia, não valida por si a assinatura digital.

Credenciais, configurações locais de ferramentas, banco de visitantes e backups não fazem parte do repositório.
