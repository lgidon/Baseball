# ⚾ Baseball Fan Hub

A lightweight, responsive web dashboard built with Python and Flask that delivers live data for any Major League Baseball team. It connects directly to the public **MLB Stats API** to aggregate real-time schedules, standings, division metrics, active rosters, and game-day ballpark weather conditions.

---

## 🏗️ Modular Architecture & Separation of Concerns

The codebase is engineered with a strict **Separation of Concerns** to enhance maintainability, scale data streams independently, and ensure the UI never suffers network-blocking lag.

* **`config.py`** — Manages user dashboard preference structures, theme states, global variables, and secure HTTP Basic Authentication locks.
* **`mlb_api.py`** — An isolated network driver containing low-level HTTP client connections targeting public `statsapi.mlb.com` endpoints.
* **`cache_manager.py`** — The state orchestrator. Houses memory locks, multi-stage repositories, and background synchronization loops.
* **`app.py`** — A lightweight Flask entry-point handling routing logic and delivering cached context blocks directly to UI layouts.

---

## ⚡ Multi-Stage Hybrid Caching Engine

To minimize external network footprints and bypass MLB API rate limits, data is parsed using a **hybrid caching engine**:

1.  **Eager Bulk Sync (Fast-Moving Data):** Game linescores, venue states, ballpark weather feeds, and divisional tables are pulled *league-wide* in single bulk requests by an automated background worker thread. These refresh dynamically every **$X$ minutes** (configured via the Admin panel).
2.  **Lazy On-Demand Sync (Slow-Moving Data):** Active team rosters (24-hour TTL expiration window) and 15-day lookahead match schedules (12-hour TTL expiration window) are pulled lazily only when a user selects a specific team, caching subsequent requests instantly.

---

## 🚀 Execution & Deployment Options

### 1. Run Natively with Python
*Best for rapid local development, layout styling tweaks, or debugging.*

* **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
* **Launch the Server with Runtime Security Environment Variables:**
    ```bash
    ADMIN_USER="admin" ADMIN_PASSWORD="yourpassword" FLASK_SECRET_KEY="devkey" python app.py
    ```
* **Access App:** Open your web browser to **`http://127.0.0.1:5000/`**

---

### 2. Build the Container via Local Dockerfile
*Best for isolated production testing or validating local infrastructure adjustments.*

* **Compile the Local Image:**
    ```bash
    docker build -t baseball-dash .
    ```
* **Launch the Container:**
    ```bash
    docker run -d -p 5000:5000 -e ADMIN_USER="admin" -e ADMIN_PASSWORD="yourpassword" baseball-dash
    ```
* **Access App:** Open your web browser to **`http://127.0.0.1:5000/`**

---

### 3. Deploy to a Kubernetes (K8s) Cluster
*Best for production simulation, automated scaling, and cluster-wide secrets management.*

* **Apply the Configuration Manifest (Includes Secrets, Deployments, and Services):**
    ```bash
    kubectl apply -f deployment.yaml
    ```
* **Access App (Standard Local Cluster IP):** Open your web browser to **`http://localhost:30080`**
* **Access App (Minikube proxy tool wrapper):** ```bash
    minikube service baseball-dash-service
    ```

---

## 🔒 Accessing the Secure Admin Page

The configuration admin dashboard is located at **`http://127.0.0.1:5000/admin`** (or port `30080` in Kubernetes). 

Upon navigating to this route, your browser will trigger an automated HTTP Basic Authentication prompt requiring the `ADMIN_USER` and `ADMIN_PASSWORD` keys injected during execution initialization. Inside this portal, you can customize layout accent themes, user greetings, and real-time cache interval rates.
