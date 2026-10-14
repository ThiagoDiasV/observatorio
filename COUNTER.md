# Contador de visitantes

Serviço Python em `visitor_counter.py`, publicado como `/opt/observatorio-monitor/site-counter.py` pela unidade `observatorio-site-counter.service`. SQLite persistente: `/var/lib/observatorio-monitor/site-counter.sqlite3`. API `/api/site-counter` por proxy Nginx para 127.0.0.1:8767.

Online: sessão com heartbeat nos últimos 60 segundos. Atualização do cliente: 20 segundos; navegadores podem suspender abas em segundo plano. Total preservado do contador instalado em 09/10/2026, não mede acessos anteriores. Pico começa em 13/10/2026; não existe dado histórico para reconstruir picos anteriores. Sessão anônima compartilhada pelas abas via localStorage; renovada após 30 minutos de inatividade. Não mede pessoas únicas nem usuários autenticados.

O contador guarda somente hash do identificador aleatório de sessão e horário da atividade, sem IP ou agente do navegador. Bloqueadores, automação e suspensão de abas podem afetar números. A API impede origens não autorizadas, mas não é mecanismo antifraude de analytics.

Validação: repetição de sessão sem aumento do total, duas sessões simultâneas, expiração da janela e permanência do pico. Publicação conferida no navegador.
