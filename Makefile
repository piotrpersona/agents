SHELL := /bin/bash
.PHONY: install lint test diff

CLAUDE_DIR ?= $(if $(CLAUDE_CONFIG_DIR),$(CLAUDE_CONFIG_DIR),$(HOME)/.claude)

install:
	./install.sh

lint:
	shellcheck install.sh statusline.sh hooks/*.sh
	uvx ruff check skills
	uvx ruff format --check skills

test:
	python3 -m unittest discover -s skills/intent-masking

# show drift between the live settings.json and repo + machine overlay
diff:
	@tmp=$$(mktemp); \
	jq -s -f merge.jq settings.shared.json "$(CLAUDE_DIR)/settings.machine.json" | jq -S . > "$$tmp"; \
	if diff -u "$$tmp" <(jq -S . "$(CLAUDE_DIR)/settings.json"); then \
	  echo "settings.json matches repo + machine overlay"; fi; \
	rm -f "$$tmp"
