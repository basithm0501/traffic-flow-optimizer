# Smart City Traffic Flow Optimization [WIP]

## Overview
This project leverages computer vision and geospatial analytics to optimize urban traffic flow using live camera feeds, weather data, and event schedules. The goal is to predict congestion and optimize traffic signal timings for smarter, safer cities.

## Why This Project Is Strong
- **Real-world impact:** Direct applications in government and smart infrastructure.
- **Skill-building:** Combines computer vision, geospatial analytics, and multi-modal data fusion.
- **Modern tech stack:** Uses Python, OpenCV, YOLOv8, GeoPandas, TensorFlow, FastAPI, Kafka, and Kepler.gl.

## Core Idea
- Ingest live traffic camera feeds and auxiliary data (weather, events).
- Detect vehicles using computer vision (YOLOv8 or Detectron2).
- Fuse geospatial, tabular, and time series data for congestion prediction.
- Optimize traffic signal timings using ML and heuristics.
- Visualize results with Kepler.gl and dashboards.

## Key Skills Learned
- **Computer Vision:** Vehicle detection with YOLOv8 or Detectron2.
- **Geospatial Analytics:** Data handling with GeoPandas, Folium.
- **Multi-modal Fusion:** Integrate CV, tabular, and time series data.
- **Streaming & APIs:** Kafka for real-time frame streaming, FastAPI for backend services.
- **Visualization:** Interactive dashboards with Kepler.gl and Streamlit/React.

## Tech Stack
- **Python**
- **OpenCV**
- **YOLOv8 / Detectron2**
- **GeoPandas, Folium**
- **TensorFlow**
- **FastAPI**
- **Kafka**
- **Kepler.gl**
- **Streamlit / React**

## Project Structure
- `apps/api/` — FastAPI backend for prediction/optimization
- `apps/dashboard/` — Streamlit/React dashboard with Kepler.gl
- `services/ingest/` — Camera frame ingestion (OpenCV/FFmpeg)
- `services/detector/` — Vehicle detection (YOLOv8/ByteTrack)
- `services/metrics/` — KPI calculation and DB writers
- `optimizer/` — Heuristic and RL-based optimization
- `sim/sumo/` — SUMO network and route simulation
- `models/forecast/` — Forecasting models
- `features/` — Weather/events data fusion
- `data/` — GeoJSON/config (small); big data via DVC
- `db/` — Database schema and migrations
- `notebooks/geo/` — Geospatial analysis notebooks

## Getting Started
1. Clone the repo and set up Python environment.
2. Start Kafka and Zookeeper with Docker Compose.
3. Add your 511NY API key to `.env`.
4. Run ingestion and detection services.
5. Explore dashboards and visualizations.

## License
MIT
