# Single autonomous Hackathon Team runtime.

.PHONY: init shared check-init up down build validate logs logs-lead logs-hub \
	logs-workers logs-verifiers sh sh-lead

TEAM ?= hackathon-team
ACCOUNT ?= foundagent
COMPOSE := TEAM=$(TEAM) ACCOUNT=$(ACCOUNT) docker compose
PY := $(shell test -x .venv-cua/bin/python && echo .venv-cua/bin/python || echo python3)

# Usage:
# make init TEAM=my-team CHALLENGE_FILE=/abs/challenge.md IDEA_CARD_FILE=/abs/idea.md
init:
	test -n "$(CHALLENGE_FILE)"
	test -n "$(IDEA_CARD_FILE)"
	$(PY) -m orchestration.team_store \
		--root state/$(TEAM) \
		--challenge-file "$(CHALLENGE_FILE)" \
		--idea-card-file "$(IDEA_CARD_FILE)"
	chmod -R ugo+rwX state/$(TEAM)

shared:
	mkdir -p state/$(TEAM)/project state/$(TEAM)/ledger \
		state/$(TEAM)/inbox state/$(TEAM)/workers \
		state/$(TEAM)/reviews state/$(TEAM)/control \
		state/$(TEAM)/sessions/lead/codex \
		state/$(TEAM)/telemetry/services state/$(TEAM)/telemetry/runs \
		accounts/$(ACCOUNT)
	chmod -R ugo+rwX state/$(TEAM)

check-init:
	test -f state/$(TEAM)/project/reference/challenge.md
	test -f state/$(TEAM)/project/reference/initial-idea-card.md

up: shared check-init
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) stop
	@docker ps -q --filter "label=hacksome.team=$(TEAM)" | while read -r id; do \
		docker stop --time 10 "$$id"; \
	done
	@docker ps -aq --filter "label=hacksome.team=$(TEAM)" | while read -r id; do \
		docker rm -f "$$id"; \
	done
	$(COMPOSE) down --remove-orphans

build:
	$(COMPOSE) build hub

validate:
	$(COMPOSE) config >/dev/null
	$(PY) -m compileall -q agent orchestration
	$(PY) -m pytest orchestration/tests/test_team_runtime.py \
		agent/tests/test_team_loadout.py -q

logs:
	$(COMPOSE) logs -f

logs-lead:
	$(COMPOSE) logs -f lead

logs-hub:
	$(COMPOSE) logs -f hub

logs-workers:
	$(COMPOSE) logs -f worker-manager

logs-verifiers:
	$(COMPOSE) logs -f verifier-manager

sh:
	$(COMPOSE) exec worker-manager sh

sh-lead:
	$(COMPOSE) exec lead bash
