# Go project structure

Use the following structure in go projects - Hexagonal architecture

Ports are interfaces owned by the core and defined by what the core needs.
Follow the Go idiom: declare each interface next to the feature that consumes
it, not in a shared `ports/` folder. Secondary (driven) adapters under
`adapters/outbound/` implement whatever interface the feature declares.

```
cmd/
    <name>/
        main.go - entry point and wiring; the only place that knows the concrete adapters and injects them into each feature
internal/
    adapters/ - adapters for the application, should contain only logic for adapting to external systems
        inbound/ - primary (driving) adapters, should contain only logic for adapting to inbound requests
            http/ - http adapters, should contain only logic for adapting to http requests
                handler.go - http handler for the application
                request_mapper.go - http request mapper for the application
                response_mapper.go - http response mapper for the application
                router.go - http router for the application
            grpc/ - grpc adapters, should contain only logic for adapting to grpc requests
                handler.go - grpc handler for the application
                server.go - grpc server for the application
        outbound/ - secondary (driven) adapters; each implements an interface declared by the feature that uses it
            postgres/ - database adapters, should contain only logic for adapting to the database, prefer using `sqlx` for database access
                migrations/ - database migrations, should contain only sql files for migrations use https://github.com/golang-migrate/migrate
                db.go - shared connection and transactor only; do not put feature queries here, each feature owns its own repository
                transaction_repository.go - satisfies create_transaction's Repository interface
            paypal/ - service adapters, should contain only logic for adapting to external services
                payment_service.go - satisfies create_transaction's PaymentService interface
                other_service.go (freeform)
    features/ - business logic for the application; depends only on models and its own interfaces
        <feature_name>/ - each feature should have its own folder, usually this will be a command like `create_transaction` or `upload_transaction`
            entrypoint.go - entrypoint for the feature, should contain the main logic for the feature
            repository.go - Repository interface, only the queries this feature needs; never shared across features, since each query could require different data
            service.go - outbound service interface, only the methods this feature needs (freeform, _service.go naming)
    models/ - models should be flat and not contain any logic (unless specified); models should be used for data transfer between layers
        transaction.go
        transaction_audit.go
    observability/ - observability for the application, should contain only logic for observability
        metrics.go - metrics for the application
        tracing.go - tracing for the application
        logging.go - logging for the application
Dockerfile - for building the application if necessary, always multistage build
```

Dependency direction: `features` depend on nothing but `models` and their own
interfaces; `adapters` depend on `features`; `main.go` wires concrete adapters
into features. If several features genuinely need the same outbound port,
prefer small duplicated interface declarations (they drift independently) over
a shared interface package.
