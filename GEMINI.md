# ShellYeah_Flask - AI Context & Instructions

## Project Overview
**ShellYeah_Flask** is a modular Flask web application designed to manage fantasy basketball leagues using the **Sleeper API**. Its primary feature is a weighted **Draft Lottery Simulator** that authentically replicates the NBA lottery system (using 1,000 combinations) to determine draft order. It also includes team analytics and trade tracking.

## Architecture & Tech Stack
*   **Language:** Python 3.10+
*   **Framework:** Flask (Modular "Application Factory" pattern)
*   **Database:** SQLite with Flask-SQLAlchemy (ORM)
*   **Frontend:** Vanilla JavaScript (ES6+), TailwindCSS, Jinja2 Templates.
*   **External API:** [Sleeper API](https://docs.sleeper.com/)
*   **Testing:** `pytest`, `pytest-mock`, GitHub Actions CI.
*   **Linting:** `pylint`.

## Directory Structure
The project follows a structured, scalable Flask layout:

*   **`run.py`**: Entry point. Creates the app instance and runs the server.
*   **`config.py`**: Configuration constants (e.g., API keys, base URLs).
*   **`app/`**: Main application package.
    *   **`__init__.py`**: Application factory function (`create_app`). Initializes DB.
    *   **`models.py`**: Database models (`League`, `Trade`, `TradeItem`, `PlayerStats`).
    *   **`api/`**: **Blueprint** for JSON API endpoints.
        *   `routes.py`: Handles `/get_leagues`, `/run_lottery`, `/analyze_trades`, etc.
    *   **`main/`**: **Blueprint** for serving HTML.
        *   `routes.py`: Serves `index.html`.
    *   **`services/`**: External API interactions.
        *   `sleeper.py`: Functions to fetch data from Sleeper (Players, Users, Leagues, Stats).
    *   **`logic/`**: Pure business logic (unit-testable).
        *   `lottery.py`: The weighted lottery simulation algorithm.
        *   `analytics.py`: Team stat calculations.
        *   `trade_analyzer.py`: Logic for syncing league history and grading trades.
    *   **`templates/`**: Jinja2 HTML templates (`index.html`).
    *   **`static/`**: Static assets (`css/style.css`, `js/main.js`).
*   **`tests/`**: Test suite.
    *   `unit/`: Tests for `logic/` (including trade analyzer).
    *   `functional/`: Tests for `api/` routes.
*   **`.github/workflows/`**: CI/CD configuration.

## Key Commands

### Development
1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run Application:**
    ```bash
    python run.py
    ```
    *Access at `http://127.0.0.1:5000`*

### Quality Assurance
1.  **Run Tests:**
    ```bash
    python -m pytest -v
    ```
2.  **Lint Code:**
    ```bash
    pylint app run.py config.py
    ```

## Development Conventions
*   **Blueprints:** All new routes should be registered via Blueprints (`api_bp` or `main_bp`), not directly on the app object.
*   **Logic Separation:** Keep route handlers (`routes.py`) thin. Move complex data processing to `app/logic/` and external API calls to `app/services/`.
*   **Frontend:** The frontend uses vanilla JS. Avoid introducing heavy frontend frameworks (React/Vue) unless necessary. Use `fetch` for API communication.
*   **Styling:** Use TailwindCSS utility classes in HTML. Custom CSS goes in `static/css/style.css`.
*   **Testing:** Write unit tests for any new logic in `app/logic`. Write functional tests for new API endpoints.

## Core Features
1.  **League Search:** Finds users and their NBA leagues via Sleeper API.
2.  **Lottery Simulator:**
    *   Uses "Previous Season" standings.
    *   Assigns odds based on 1,000 combinations.
    *   Handles ties by splitting odds.
3.  **Analytics:** Calculates average age, positional breakdown, and scoring stats.
4.  **Trade Grading & History:**
    *   **Net Grading:** Calculates "Win/Loss" grades for every trade based on the Net Fantasy Points of assets exchanged.
    *   **History Sync:** Automatically syncs and links previous league seasons to build a complete multi-year timeline.
    *   **Pick Resolution:** Intelligently resolves traded Draft Picks to the actual players selected (using historical Draft Results) and includes their stats in the trade valuation.
    *   **Visual Timeline:** Displays an interactive, chronological feed of all transactions.
