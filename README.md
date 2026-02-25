# FloodSense — AI-Powered Flood Prediction System

![Java](https://img.shields.io/badge/Java-21-orange)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-4.0.3-green)
![React](https://img.shields.io/badge/React-18-blue)
![Python](https://img.shields.io/badge/Python-3.12.10-yellow)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)

> A full-stack flood risk prediction platform combining real-time weather data,
> river gauge monitoring, and machine learning to deliver actionable flood risk alerts.

## Quick Start
```bash
git clone https://github.com/Codeglenn/floodsense.git
cd floodsense
docker-compose -f infrastructure/docker-compose.yml up
```
Then open http://localhost:3000

## Services
| Service     | Technology       | Port |
|-------------|------------------|------|
| Frontend    | React + Tailwind | 3000 |
| Backend API | Spring Boot      | 8080 |
| ML Service  | Python + FastAPI | 8000 |
| Database    | PostgreSQL       | 5432 |

## Project Structure
```
floodsense/
├── backend/          # Spring Boot REST API
├── frontend/         # React application  
├── ml-service/       # Python ML pipeline + FastAPI
├── infrastructure/   # Docker Compose + Nginx config
└── docs/             # Architecture diagrams, API spec

```
## Steps to run Spring boot backend
```bash
cd backend
mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=devs
```

## Steps to run python ml-service
```bash
cd ml-service
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
jupyter notebook
python -m app.services.data_fetcher
```