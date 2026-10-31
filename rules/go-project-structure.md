# Go project structure

Use the following structure in go projects - Hexagonal architecture

```
cmd/
    <name>/
        main.go - entry point for the application and wiring
internal/
    adapters/ - adapters for the application, should contain only logic for adapting to external systems
        inbound/ - adapters for inbound requests, should contain only logic for adapting to inbound requests
            http/ - http adapters, should contain only logic for adapting to http requests
                handler.go - http handler for the application
                request_mapper.go - http request mapper for the application
                response_mapper.go - http response mapper for the application
                router.go - http router for the application
            grpc/ - grpc adapters, should contain only logic for adapting to grpc requests
                handler.go - grpc handler for the application
                server.go - grpc server for the application
        outbound/
            postgres/ - database adapters, should contain only logic for adapting to the database, prefer using `sqlx` for database access
                migrations/ - database migrations, should contain only sql files for migrations use https://github.com/golang-migrate/migrate
                db.go - shared connection and transactor only; do not put feature queries here, each feature owns its own repository
            paypal/ - service adapters, should contain only logic for adapting to external services
                transaction_service.go - service for transactions
                other_service.go (freeform)
    features/ - business logic for the application
        <feature_name>/ - each feature should have its own folder, usually this will be a command like `create_transaction` or `upload_transaction`
            entrypoint.go - entrypoint for the feature, should contain the main logic for the feature
            repository.go - feature-specific database repository; each feature owns its queries and must not share a repository across features, since each query could require different data
    models/ - models should be flat and not contain any logic (unless specified); models should be used for data transfer between layers
        transaction.go
        transaction_audit.go
    observability/ - observability for the application, should contain only logic for observability
        metrics.go - metrics for the application
        tracing.go - tracing for the application
        logging.go - logging for the application
    ports/ - interfaces for the application, should contain only interfaces and no logic
        transaction_service.go - service are _service.go - for external calling
        other_port.go (freeform)
        note: db repositories are not shared ports; each feature declares its own repository interface next to its entrypoint.go
Dockerfile - for building the application if necessary, always multistage build
```
