# GenHealth AI DME Order Management — Backend

Flask REST API for managing DME orders with AI-powered PDF data extraction.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment template:
   ```bash
   cp .env.example .env
   ```

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the development server:
   ```bash
   flask run
   ```

## Testing

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```
