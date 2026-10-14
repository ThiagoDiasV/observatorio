# Pesquisa diária com revisão editorial

`collect.py` consulta feeds configurados em `sources.json`, aplica apenas um filtro de relevância e cria arquivos em `inbox/`. Cada item nasce com `status: needs_review` e `publication_allowed: false`.

O coletor não altera `cases.json`, `statements.json`, PDFs, páginas estáticas ou o diretório público. Isso é intencional: uma manchete, uma denúncia ou uma fala sem contexto não pode virar publicação automática.

## Fluxo de trabalho

1. O timer executa a coleta às 06:00, com atraso aleatório de até 15 minutos.
2. Um editor confirma fonte, data, contexto, resposta e situação processual no painel privado.
3. Após aprovar, o editor completa a ficha estruturada. A validação exige fonte HTTPS, pessoas, data, situação, resumo, desfecho e resposta.
4. O comando `editorial_pipeline.py create-changeset` reúne apenas fichas marcadas como prontas. O comando `stage` copia uma fonte editorial para uma área isolada, gera o site e executa a verificação.
5. Somente depois da conferência humana do staging, uma pessoa autorizada pode executar `deploy_release.sh` sobre aquela cópia. O deploy cria um release completo, valida-o e só então muda o symlink público.

## Instalação na VPS

O diretório de trabalho deve ficar em `/opt/observatorio`, separado de `/var/www/bozo/releases/`. Criar o usuário de serviço `observatorio`, instalar os arquivos `.service` e `.timer` em `/etc/systemd/system/`, executar `systemctl daemon-reload` e habilitar `observatorio-collect.timer`.

O usuário de serviço não deve ter permissão de escrita no diretório público do Nginx. A publicação deve ser uma ação separada, auditada e com rollback por release.

## Publicação separada

`deploy_release.sh` só pode ser executado depois de uma revisão editorial e dos testes `build.py` e `verify.py`. Ele gera um diretório de release novo e troca o symlink de forma atômica; o coletor diário não chama esse script e não possui essa permissão.

## Painel privado de revisão

`review_server.py` atende somente em `127.0.0.1:8787`. Ele grava decisões em `automation/review/decisions.json`, exige uma justificativa para aprovar ou rejeitar e fixa `publication_allowed: false` em toda decisão. Para acessar sem expor uma porta pública, use um túnel SSH:

```sh
ssh -L 8787:127.0.0.1:8787 root@SEU_IP
```

Depois, abra `http://127.0.0.1:8787` no navegador local. O painel registra decisões e rascunhos em `automation/review/`; não possui botão de publicação pública.

## Saúde e backup

`observatorio-health.timer` produz `automation/monitoring/latest.json` após a coleta e verifica fontes, idade da fila e HTTPS público. Falha total de fontes, atraso superior a 30 horas ou indisponibilidade do site são gravados como alertas no relatório e no log, sem interromper o agendamento seguinte.

`observatorio-backup.timer` cria um arquivo diário em `/var/backups/observatorio`, contendo fila, estado, decisões, rascunhos e monitoramento. Mantém 30 dias. Esses backups não incluem o release público, que já permanece versionado em `/var/www/bozo/releases/`.
