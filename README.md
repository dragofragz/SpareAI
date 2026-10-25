---
title: SpareAI - AI Spare Parts & Service Assistance
emoji: 🔧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# SpareAI — AI-Based Spare Parts E-Commerce & Field Service Assistance

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-005571.svg)](https://fastapi.tiangolo.com/)
[![SBERT](https://img.shields.io/badge/AI-Sentence--BERT-orange.svg)](https://www.sbert.net/)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)

**Final Year Engineering Project (B.Tech Computer Science & Engineering)**  
**Group 09 · College of Engineering Cherthala, Kerala**  
**Academic Base Research Paper:**  
> Schiavo, F., et al., *"On Predicting Spare Parts for Field Services by Leveraging Fault Description and Historical Repairing Data"*, **IEEE Access**, 2024.

---

## 1. Project Overview

**SpareAI** bridges the gap between unstructured vehicle fault complaints and automated spare parts fulfillment. Vehicle owners often describe problems using colloquial, non-technical language (*"Loud grinding/knocking noise from underbody when turning over speed bumps"*). 

SpareAI utilizes **Sentence-BERT (`all-MiniLM-L6-v2`)** embeddings combined with **Case-Based Reasoning (CBR)** over historical repair cases to:
1. Infer the exact failed spare part with a confidence percentage.
2. Provide transparent **explainability** (*"why this was recommended"* based on past similar repairs).
3. Provide **AI Service Guidance (DIY vs Professional Technician)** based on repair complexity, specialized tools, and safety risks.
4. Validate fitment compatibility against vehicle make, model, and year range.
5. Provide multi-supplier real-time stock visibility with a dedicated **Supplier Merchant Portal**.
6. Offer end-to-end e-commerce ordering with direct workshop delivery.
7. Display nearby workshops and suppliers on an interactive GPS map using Leaflet and the Haversine formula.
8. Provide curated, embedded DIY repair tutorial videos with tool requirements checklists.

---

## 2. Quick Setup & Execution

### Prerequisites
- Python 3.10 or higher
- Internet connection (for first-time download of the lightweight SBERT model ~80MB, and CDN assets)

### One-Command Setup & Run
Open your terminal (PowerShell or Bash) in the project root:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed database & compute SBERT embeddings
python seed.py

# 3. Start development server
uvicorn app.main:app --reload
```

Once running, access the web app at: **`http://127.0.0.1:8000`**

---

## 3. Demo Credentials

| Role | Email | Password | Pre-loaded Context |
| :--- | :--- | :--- | :--- |
| **Customer / Owner** | `demo@example.com` | `demo123` | Hyundai i20 (2020, Car) & Royal Enfield Classic 350 (2019, Bike) |
| **Parts Supplier** | `supplier@example.com` | `supplier123` | Cherthala Auto Spares & Distributor (manages shop info, GPS, stock) |
| **Enterprise Admin** | `admin@example.com` | `admin123` | Dedicated executive portal (`/admin/login`) with global audit & telemetry |

---

## 4. Suggested 5-Minute Live Teacher Presentation Script

Follow this sequence during your project evaluation to demonstrate every feature end-to-end:

### Minute 1: Login & Garage Management
1. Navigate to `http://127.0.0.1:8000/login` and log in with `demo@example.com` / `demo123`.
2. Point out the **Garage Dashboard**:
   - The two registered vehicles (Hyundai i20 4-wheeler and Royal Enfield Classic 350 2-wheeler).
   - The quick "+ Add Vehicle" inline form supporting cars and bikes.

### Minute 2: Natural Language Fault Input & AI Inference
1. On the **Hyundai i20** card, click **"Diagnose Problem"**.
2. On the fault description screen, explain how users don't need technical jargon.
3. Click the first pre-filled sample prompt:
   > *"Loud grinding noise from underbody when turning over speed bumps"*
4. Click **"Analyze with AI"** (show the loading spinner while SBERT vectorizes the text and queries the CBR database).

### Minute 3: Explainable AI Diagnosis, DIY Assessment & Fitment Check
1. The **AI Diagnosis & Part Recommendation Dashboard** renders:
   - Selected vehicle with green **"Verified"** badge.
   - User's symptom in a quote block.
   - Recommended Component: **Front Lower Control Arm Suspension Assembly**.
   - **Confidence Bar**: High match (~99%).
   - **AI Service Assistance & Complexity Check**: Shows whether the user can do it themselves or requires a certified technician based on task complexity (e.g., Lower Control Arm highlights *"Professional Technician Required"* due to steering alignment & ball joint pressing).
   - **Explainability Block**: Explain to your teacher that the system shows verbatim historical repair cases that shared high cosine similarity with the prompt.
   - **Fitment Check**: Green badge showing 100% compatibility with Hyundai i20 (2020).
   - **Cross-Supplier Stock Status**: Point out supplier availability (e.g. out of stock at Hub 1, but in stock at nearby Hub 2).

### Minute 4: E-Commerce, Workshop Delivery & Live Order Tracking
1. Click **"Buy Part Now"** &rarr; inspect product specifications and tool checklist &rarr; click **"Add to Cart"**.
2. Go to **Cart** &rarr; click **"Proceed to Checkout"**.
3. Select **"Deliver to Workshop"** dropdown &rarr; choose *Cherthala Modern Car Care*.
4. Click **"Confirm & Place Order"**.
5. You are taken to the **Live Order Tracking Timeline** (`Placed -> Confirmed -> Shipped -> Delivered`).
6. Click the orange presentation button: **"Advance to Confirmed"** and **"Advance to Shipped"** to demonstrate real-time tracking status updates without page breakage.

### Minute 5: Field Service Workshop Locator & Tutorial Guides
1. Click **"Workshops"** in the top navigation:
   - Show the interactive **Leaflet Map** with OpenStreetMap tiles.
   - Show Blue pins (Certified Workshops) and Green pins (Spare Parts Suppliers) centered around Cherthala/Alappuzha/Kochi.
   - Point out Haversine-calculated road distances, ratings, and the "Navigate &rarr;" link that opens directions in Google Maps.
2. Click **"Tutorial"** for any part:
   - Show the embedded YouTube repair guide, repair difficulty level (Easy/Medium/Hard), and required tools checklist.
3. Switch user:
   - Log in as **Supplier** (`supplier@example.com` / `supplier123`): Demonstrate the **Supplier Portal**, shop GPS setup, catalog management, and live inventory stock adjustments.
   - Log in as **Enterprise Admin** (`admin@example.com` / `admin123` at `/admin/login`): Demonstrate the executive KPI console, AI inference diagnostics, master user directory, and order status override controls.
4. Conclude on the **"About"** page showcasing the architecture diagram and base paper citation.

---

## 5. Verification & Accuracy Evaluation

### Automated PyTest Verification
Run the automated test suite verifying both the AI logic and REST API:
```bash
pytest test_recommend.py -v
```
Checks:
- `test_lower_control_arm_recommendation`: Confirms "grinding noise from underbody" returns Lower Control Arm for Hyundai i20.
- `test_bike_chain_recommendation`: Confirms two-wheeler symptoms recommend Drive Chain & Sprocket.
- `test_api_recommend_endpoint`: Validates the `/api/recommend` JSON REST response.

### Leave-One-Out Evaluation Script
To quote statistical accuracy metrics in your final presentation and project report, run:
```bash
python evaluate.py
```
This performs a rigorous leave-one-out cross-validation across all 80 repair cases in the case base, reporting:
- **Top-1 Recommendation Accuracy**: 26.25% (21/80)
- **Top-3 Recommendation Accuracy**: 58.75% (47/80)
- **Two-Wheeler / Bike Category Top-3**: 74.07% (20/27)
- Individual breakdown across Cars and Bikes with exact presentation quotes ready for your viva.

---

## 6. Architecture & Database Design

```
                     ┌───────────────────────────────┐
                     │   User Fault Description      │
                     │  (e.g. "grinding over bumps") │
                     └───────────────┬───────────────┘
                                     │
                                     ▼
                     ┌───────────────────────────────┐
                     │     Sentence-BERT Encoder     │
                     │      (all-MiniLM-L6-v2)       │
                     └───────────────┬───────────────┘
                                     │ 384-dim vector
                                     ▼
                     ┌───────────────────────────────┐
                     │   Cosine Similarity Search    │
                     │  against RepairCase Case Base │
                     └───────────────┬───────────────┘
                                     │ Top-k Cases + Domain Boost
                                     ▼
                     ┌───────────────────────────────┐
                     │   Similarity-Weighted Voting  │
                     │    Candidate Part Ranking     │
                     └───────────────┬───────────────┘
                                     │
               ┌─────────────────────┴─────────────────────┐
               ▼                                           ▼
┌───────────────────────────────┐           ┌───────────────────────────────┐
│     PartCompatibility Check   │           │      Supplier Stock Lookup    │
│  (Make, Model, Year Range)    │           │    (Multi-distributor availability)
└───────────────────────────────┘           └───────────────────────────────┘
```

### Database Tables (Normalized SQLite)
- **`User`**: `user_id`, `name`, `email`, `password_hash`, `contact`, `address`, `is_admin`
- **`Vehicle`**: `vehicle_id`, `user_id` (FK), `type` (car/bike), `make`, `model`, `year`, `vin`
- **`Fault`**: `fault_id`, `vehicle_id` (FK), `description`, `category`, `created_at`
- **`SparePart`**: `part_id`, `part_name`, `oem_code`, `price`, `category`, `supplier_id` (FK), `stock_qty`, `image_url`, `video_id`, `difficulty`, `tools_required`
- **`PartCompatibility`**: `id`, `part_id` (FK), `make`, `model`, `year_from`, `year_to`
- **`RepairCase`**: `case_id`, `symptoms`, `vehicle_type`, `make`, `model`, `solution_part_id` (FK), `embedding` (BLOB)
- **`Supplier`**: `supplier_id`, `name`, `lat`, `lng`, `address`, `contact`
- **`Workshop`**: `workshop_id`, `name`, `lat`, `lng`, `address`, `contact`, `verified`, `rating`
- **`Order`**: `order_id`, `user_id` (FK), `workshop_id` (FK nullable), `status`, `total`, `created_at`
- **`OrderItem`**: `id`, `order_id` (FK), `part_id` (FK), `qty`, `price`

---

## 7. Replacing Free Tiers with Production Cloud APIs

For the academic demo, SpareAI uses zero-cost, keyless technologies (**OpenStreetMap + Leaflet**, and curated YouTube video IDs) to guarantee reliability during evaluation without quota failures.

In an enterprise production deployment:
1. **Google Maps JavaScript API & Places API**:
   - In `app/templates/workshops.html`, replace Leaflet with:
     ```html
     <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_KEY&callback=initMap" async defer></script>
     ```
   - Replace the Leaflet `L.map` initialization with `new google.maps.Map(document.getElementById("map"), {...})` and `google.maps.Marker`.
   - Use Google Distance Matrix API for real-time traffic-aware road routing instead of great-circle Haversine.
2. **YouTube Data API v3**:
   - In `app/routes/tutorials.py`, invoke the YouTube Data API endpoint:
     `GET https://www.googleapis.com/youtube/v3/search?part=snippet&q={part_name}+replacement+tutorial&key=YOUR_YOUTUBE_API_KEY`
   - Dynamically retrieve the top video ID and description instead of querying the curated `SparePart.video_id` column.

---

## 8. Authors & Acknowledgements

- **Students**: Final Year B.Tech Project Group 09
- **Institution**: College of Engineering Cherthala (CEC), Kerala, India
- **Reference**: Schiavo et al., *IEEE Access*, 2024.
