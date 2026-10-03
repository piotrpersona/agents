# Coding

## Coding Style

- Code should be self-explanatory and readable, avoid using comments to explain code unless asked to do so.
- always init using .gitignore
- Prefer using Golang for CLIs and production applications, use Python for scripts and data processing tasks
- Never log sensitive information, always use log levels and structured logging
- logs should be structured and emitted through the OpenTelemetry logs bridge, never hand-rolled JSON
- use OTEL instrumentation from official SDK
- prefer using integration e2e tests over unit tests
- use testcontainers for integration tests, avoid using mocks for integration tests if possible - mock external 3rd party calls
- in integration tests ensure that each test suite has its own database/namespace to avoid overlapping tests
- implement unit test for complex  logic and edge cases, use table driven tests for unit tests
- prefer configuration via .env file - always add .env.example file with all the required environment variables and their default values, use `godotenv` for loading .env files in Go projects
- always add .env to .gitignore
- abstain from retries in production code, use retries only in scripts and data processing tasks - unless specified
- use Makefile for repetitive work
    - make lint - run linter on codebase
    - make gen - generate code

## Git

- always use `git commit` with `-sm` flag and write meaningful commit messages but short
- always use `git rebase` instead of `git merge` for merging branches, avoid using `git merge` unless specified 
- use conventional commits for commit messages
    - feat:, fix:, docs:, style:, refactor:, perf:, test:, chore:
    - use branch naming convention for branches - feature/<feature_name>, bugfix/<bug_name>, hotfix/<hotfix_name>, chore/<chore_name>, refactor/<refactor_name>, docs/<docs_name>, research/<research_name>
    - prefer using `/caveman-commit` skill for generating commit messages
- before opening PRs prompt user to verify PR message
    - output suggested markdown message in console
    - do not use `/caveman` skill for outputing PR messages
    - in PR always add these sections What, Why, Testing
- never push to main/master - unless the repo allows for it in Agents/Claude .md files

## Go

- prefer Go via `asdf` tool latest version
- always format code using `gofumpt`
- never leave built binaries in the working tree: use `go run` locally, and `go build` only inside a Docker multistage build
- use golangci-lint for linting
- omit using generics unless necessary, prefer using interfaces and composition over generics
- if querying a database in bulk prefer using fan-out pattern with goroutines and channels, do not use `IN` queries for large datasets
- always use transcations - define transactor interface in the repository layer and implement it in the database adapter layer, use `sqlx` for database access, that would wrap the `*sqlx.DB` and `*sqlx.Tx` and provide a `Transact` method that would accept a function and run it in a transaction, if the function returns an error the transaction is rolled back, otherwise it is committed
- db migrations must be tested within the integration tests of the code
- prefer using `context.Context` for all functions that can be cancelled or have a timeout, do not use `context.Background()` or `context.TODO()` in production code
- do not use Depedency Injection frameworks, use constructor injection instead
- prefer using `errgroup.Group` from `golang.org/x/sync/errgroup` for concurrent operations, unless specified
- use signal.NotifyContext instead of context.WithCancel for graceful shutdown - always shutdown the application gracefully, do not use os.Exit() or panic() for shutdown
- never panic and log.Panic/Fatal, always return errors and handle them gracefully
- prefer using switch-case with exhaustive cases (unless specified) over dynamic maps
- prefer using newest go syntax and features, avoid using deprecated features
- use OpenTelemetry for tracing and metrics, use `otel` package for tracing and metrics, use `otelhttp` for http tracing and metrics, use `otelsql` for sql tracing and metrics, use `otelgrpc` for grpc tracing and metrics
- use zap for logging, bridged to OTEL via `otelzap`
- when implementing an interface always check that struct implements interface
- abstain from using init() function - unless specified

## Python

- use uv
- always use typed Python
- use Pydantic for data validation and parsing
- use structlog for logging
- use FastAPI for building APIs
- always format code with `black` and lint with `ruff`

## Openrouter

- always use OpenRouter for LLMs, avoid using OpenAI directly
- use official language SDK
- when using more than one model within a project, always define a model registry and use it to get the model by name
