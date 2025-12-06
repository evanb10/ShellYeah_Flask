# Running Tests

I have set up a test suite using `pytest`.

## 1. Install Dependencies

Ensure you have the test dependencies installed:

```bash
pip install -r requirements.txt
```

## 2. Run Tests

To run all tests, execute:

```bash
python -m pytest
```

## Test Structure

- **tests/unit/**: Tests for pure business logic (`app/logic/`) which do not require a Flask context or database.
- **tests/functional/**: Tests for API endpoints (`app/api/`) and routes, using mocked external services.
