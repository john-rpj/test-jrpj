.PHONY: help dev test deploy-local destroy-local deploy-vercel destroy-vercel deploy-railway destroy-railway status

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Development ---
dev:              ## Run app locally with hot reload
	npm run dev

test:             ## Run tests
	npm test

# --- Deployment ---
deploy-local:     ## Deploy to local
	cd infra/local && uv sync && pulumi up --yes

deploy-vercel:     ## Deploy to vercel
	cd infra/vercel && uv sync && pulumi up --yes

deploy-railway:     ## Deploy to railway
	cd infra/railway && uv sync && pulumi up --yes

# --- Teardown ---
destroy-local:    ## Tear down local deployment
	cd infra/local && uv sync && pulumi destroy --yes

destroy-vercel:    ## Tear down vercel deployment
	cd infra/vercel && uv sync && pulumi destroy --yes

destroy-railway:    ## Tear down railway deployment
	cd infra/railway && uv sync && pulumi destroy --yes

# --- Operations ---
status:           ## Show deployment status
	@echo "=== local ===" && (cd infra/local && pulumi stack output 2>/dev/null || echo "Not deployed")
	@echo "=== vercel ===" && (cd infra/vercel && pulumi stack output 2>/dev/null || echo "Not deployed")
	@echo "=== railway ===" && (cd infra/railway && pulumi stack output 2>/dev/null || echo "Not deployed")
