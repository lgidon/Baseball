# ⚾ Baseball Fan Hub

A lightweight, responsive web dashboard built with Python and Flask that delivers live data for any Major League Baseball team. It connects directly to the public **MLB Stats API** to aggregate real-time schedules, standings, division metrics, active rosters, and game-day ballpark weather conditions.

---

## 🚀 Execution & Deployment Options

### 1. Run Natively with Python
*Best for rapid local development, styling tweaks, or debugging code.*

* **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
* **Launch the Server:**
    ```bash
    python app.py
    ```
* **Access App:** Open your web browser to **`http://127.0.0.1:5000/`**

---

### 2. Pull the Pre-Built Image from Docker Hub
*Best for instant execution without needing Python or the source files stored locally.*

* **Pull and Run the Container:**
    ```bash
    # Replace 'yourusername' with your actual Docker Hub registry username
    docker run -d -p 5000:5000 yourusername/baseball-dash:latest
    ```
* **Access App:** Open your web browser to **`http://127.0.0.1:5000/`**

---

### 3. Build the Container via Local Dockerfile
*Best for isolated production testing or validating local architecture changes.*

* **Compile the Local Image:**
    ```bash
    docker build -t baseball-dash .
    ```
* **Launch the Container:**
    ```bash
    docker run -d -p 5000:5000 baseball-dash
    ```
* **Access App:** Open your web browser to **`http://127.0.0.1:5000/`**

---

## 🛠️ Architecture & Core Feature Set

The interface renders an optimized, mobile-responsive **4-Quadrant Grid** designed for quick readability:

* **Quadrant 1: Live Scoreboard & Weather** Real-time game states (linescores, current innings) coupled with live ballpark atmospheric metrics (temperature, conditions, wind velocity) pulled dynamically via the active venue's game feed.
* **Quadrant 2: Upcoming Schedule** A forward-looking lookahead tracking the selected team's next 5 matches, locations, and home/away orientations over the upcoming weeks.
* **Quadrant 3: Division Standings** Contextual division tables detailing Wins, Losses, and Games Back (GB) metrics with your selected team highlighted inline for immediate context.
* **Quadrant 4: Active Team Roster** A height-stabilized, scrollable panel matching active squads with custom color badges mapping position classes (e.g., Pitchers vs. Position Players).

---

## ⚙️ Persistent Configurations & Future Backlog
*As this project advances, we are tracking the following architectural scaling benchmarks:*

- [ ] **State Management & Session Persistence:** Integrate Flask-Session or browser local storage so the dashboard implicitly remembers a user's chosen team across page refreshes and browser restarts.
- [ ] **API Caching Layer:** Implement server-side caching (e.g., Flask-Caching) for slow-moving data points like Standings and Rosters to drastically reduce external network overhead.
- [ ] **Player Metrics Lookup:** Inject click events on the active roster list to dynamically fetch individual player season logs and stat cards.
