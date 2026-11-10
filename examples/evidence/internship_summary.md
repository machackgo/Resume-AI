# Fictional Freight Co. — internship summary (synthetic)

## Ticket classification service
I built a FastAPI service that routes inbound support tickets into 9 queues with a scikit-learn classifier.
Predictions and audit rows are stored in PostgreSQL. The service ran on a single Docker host.

## Testing
I added pytest unit and integration tests and a GitHub Actions workflow that blocks merges when tests fail.
