.PHONY : clear_cache
clear_cache :
	python -m shortcuts.Makefile.clr_cache

.PHONY : move_logs
move_logs :
	python -m shortcuts.Makefile.mov_logs

.PHONY : pytest
pytest : 
	pytest ./tests

.PHONY : TLS
TLS :
	openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes \
		-keyout vault/tls/private.crt \
		-out vault/tls/public.crt \
		-subj "/CN=Entertainment_domain" \
		-addext "subjectAltName=DNS:Entertainment_domain,DNS:localhost,DNS:vault.sora.svc,IP:127.0.0.1,DNS:vault_1,DNS:vault_2,DNS:vault_3"

COMPOSE = docker compose -f vault/docker-compose.yml

.PHONY : vault_up
vault_up :
	$(COMPOSE) up -d

.PHONY : vault_down
vault_down :
	$(COMPOSE) down

.PHONY : vault_logs
vault_logs :
	$(COMPOSE) logs -f

.PHONY : vault_restart
vault_restart :
	$(COMPOSE) restart

.PHONY : vault_delete
vault_delete :
	$(COMPOSE) down -v

.PHONY : vault_init
vault_init :
	$(COMPOSE) exec vault_server_1 vault operator init -address=https://127.0.0.1:8200

.PHONY : vault_unseal
vault_unseal :
	python vault/unseal.py