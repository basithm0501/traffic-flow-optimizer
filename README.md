
# Smart City Traffic Flow Optimization


## Overview
This project leverages computer vision, geospatial analytics, time series forecasting, and reinforcement learning to optimize urban traffic flow using live camera feeds, weather data, and event schedules. The pipeline predicts congestion, forecasts traffic KPIs, and optimizes signal timings for smarter, safer cities.


## Why This Project Is Strong
- **Real-world impact:** Direct applications in government, smart infrastructure, and urban planning.
- **Skill-building:** Combines computer vision, geospatial analytics, time series forecasting, RL, and multi-modal data fusion.
- **Modern tech stack:** Python, OpenCV, YOLOv8, GeoPandas, XGBoost, SUMO, FastAPI, Kafka, Kepler.gl, and more.


## Core Pipeline
- Ingest live traffic camera feeds and auxiliary data (weather, events)
- Detect vehicles using computer vision (YOLOv8/Detectron2)
- Enrich features with weather and event data
- Fuse geospatial, tabular, and time series data for congestion prediction
- Forecast traffic KPIs (queue length, speed, volume) using XGBoost and baseline models
- Automated reporting of model results and metrics
- (WIP) Visualize results with Folium, Kepler.gl, and dashboards
- (WIP) Optimize traffic signal timings using RL (SUMO simulation)


## Key Skills & Modules
- **Computer Vision:** Vehicle detection with YOLOv8/Detectron2
- **Geospatial Analytics:** Road network modeling, camera FOV overlays, metrics mapping
- **Feature Engineering:** Weather/event enrichment, lag creation, missing data handling
- **Time Series Forecasting:** Baseline, XGBoost, LightGBM, automated reporting
- **Reinforcement Learning:** SUMO simulation, RL agent for adaptive signal control
- **Streaming & APIs:** Kafka for real-time metrics, FastAPI for backend services
- **Visualization:** Folium, Kepler.gl, Streamlit/React dashboards


## Tech Stack
- **Python**
- **OpenCV, YOLOv8 / Detectron2**
- **GeoPandas, Folium, Kepler.gl**
- **XGBoost, LightGBM**
- **SUMO, TraCI, RLlib (optional)**
- **FastAPI, Kafka**
- **Streamlit / React**


## Project Structure
- `apps/api/` — FastAPI backend for prediction/optimization
- `apps/dashboard/` — Streamlit/React dashboard with Kepler.gl
- `services/ingest/` — Camera frame ingestion (OpenCV/FFmpeg)
- `services/detector/` — Vehicle detection (YOLOv8/ByteTrack)
- `services/metrics/` — KPI calculation and DB writers
- `features/` — Weather/events data fusion
- `models/forecast/` — Baseline and ML forecasting models, automated reporting
- `optimizer/` — Heuristic and RL-based optimization (SUMO RL agent, training loop)
- `sim/sumo/` — SUMO network, route, and config files for simulation
- `data/` — GeoJSON/config (small); big data via DVC
- `db/` — Database schema and migrations
- `notebooks/geo/` — Geospatial analysis, feature engineering, and visualization
- `reports/` — Automated markdown reports of model results


## Getting Started
1. Clone the repo and set up Python environment
2. Start Kafka and Zookeeper with Docker Compose
3. Add your 511NY API key to `.env`
4. Run ingestion and detection services
5. Run feature enrichment and forecasting scripts
6. Explore geospatial notebooks and dashboards
7. (Optional) Run SUMO RL agent for adaptive signal control
8. Review automated reports in `reports/`


## License
MIT
