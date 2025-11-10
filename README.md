# ShellYeah_Flask
Recreating the ShellYeah_FantasyBasketball repo using Flask instead of Django. 

🏀 ShellYeah! Fantasy Lottery

This is a web application that runs a true-to-life NBA-style draft lottery for your Sleeper fantasy basketball league.

Tired of using a basic random number generator that doesn't feel exciting or fair? This tool imports your league's previous season standings to set the odds, then runs a weighted lottery simulation—complete with a "card reveal"—to determine the new draft order.

Project Goal

The goal of this project is to provide fantasy basketball commissioners with a fair, transparent, and exciting way to determine their league's draft order. It replaces simple, unweighted "randomizers" with the official weighted NBA lottery system (based on 1,000 combinations) to give the worst teams from the previous season the best chance at the #1 pick.

Key Features

Sleeper API Integration: Securely finds any user's Sleeper account by username.

Automatic League Importing: Fetches all of a user's NBA leagues for the current season.

Previous Season Standings: Automatically finds the linked previous season and pulls the regular season standings.

Automatic Seeding: Sorts the non-playoff teams by their record (and points for as a tie-breaker) to create the official lottery seeds.

Weighted Odds: Pre-fills the lottery odds based on the official 2025 NBA 14-team lottery (140 combinations for #1, etc.).

Authentic Lottery Logic: Runs a simulation of the 4-pick draw using 1,000 combinations, exactly how the NBA does it. A team's odds directly correspond to how many of the 1,000 combinations they own.

Exciting Reveal: Presents the final draft order with the top 4 picks "sealed" in face-down cards, allowing you to reveal them one by one for maximum suspense.

How It Works (Technical Overview)

This project is built with a simple Python backend and a single-page JavaScript frontend.

Backend (app.py): A Flask (Python) server that:

Serves the main index.html file.

Provides API endpoints (e.g., /get_leagues, /get_lottery_teams, /run_lottery).

Handles all communication with the external Sleeper API to fetch user, league, and roster data.

Contains the core perform_nba_lottery function that runs the weighted combination simulation.

Frontend (index.html): A single HTML file using Tailwind CSS and vanilla JavaScript:

Provides a clean, multi-step user interface.

Makes fetch requests to its own Flask backend to get data and run the lottery.

Dynamically renders the team lists, odds, and the final "card reveal" grid.

How to Run

Prerequisites:

Make sure you have Python 3 installed.

Download & Setup:

Clone this repository or download the files (app.py, index.html, requirements.txt) into a new folder.

Open your terminal or command prompt and navigate to that folder.

Create a Virtual Environment (Recommended):

python -m venv venv


Activate the environment:

Windows: .\venv\Scripts\activate

macOS/Linux: source venv/bin/activate

Install Dependencies:
With your virtual environment active, install the required Python packages:

pip install -r requirements.txt


Run the Flask Server:
In the same terminal, run the main application file:

python app.py


You should see output indicating the server is running on http://127.0.0.1:5000.

Open the App:
Open your web browser and go to:
http://127.0.0.1:5000

You can now use the simulator!

Demo

(Suggestion: Record a quick GIF of the app in action—from entering a username to revealing the final pick—and embed it here!)

[Insert your GIF or screenshot here]
