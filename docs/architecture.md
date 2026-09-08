# Architecture Note

```text
Browser
  |
  v
Flask routes / server-rendered HTML
  |
  +--> Flow Engine --> Declarative country/customer journey
  |
  +--> Validation
  |
  +--> Integration adapters --> deterministic mocks
  |          |
  |          +--> identity / address / sanctions / affordability
  |          +--> credit / registry / representative / UBO
  |          +--> business profile / business credit / bank account
  |
  +--> Decisioning --> approved | manual_review | rejected
  |
  v
SQLite
  +--> applications
  +--> steps
  +--> integration_results
  +--> audit_events
```

The main senior-level design choice is separation of concerns. Country-specific requirements live in configuration. Provider-specific behavior lives behind integration functions. Decision policy is independent from HTTP and persistence. This keeps the system easy to extend when another country, customer type or provider is introduced.
