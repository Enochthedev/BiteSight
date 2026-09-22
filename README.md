# 🍽️ BiteSight

**Snap a photo of a Nigerian meal and get instant feedback on what's missing from your plate.** A FastAPI + PyTorch backend recognises local dishes (amala, eba, moimoi, jollof and 100 more), maps them to food groups, and returns a balance score with culturally relevant suggestions to an Expo mobile app.

![Python](https://img.shields.io/badge/Python-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-MobileNetV2-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![Expo](https://img.shields.io/badge/Expo-React_Native-000020?style=flat-square&logo=expo&logoColor=white)
![Postgres](https://img.shields.io/badge/PostgreSQL-Redis-336791?style=flat-square&logo=postgresql&logoColor=white)

<p align="center">
  <img src="docs/images/web-demo-upload.jpg" alt="BiteSight web demo: a photo of akara and bread ready to analyse" width="480" />
  <br />
  <sub>The bundled web demo (<code>frontend/index.html</code>). The Expo app in <code>mobile/</code> is the main client.</sub>
</p>

## Why this exists

Generic calorie apps don't recognise *eba and egusi* or *boiled yam and egg*, and their advice assumes a Western plate. BiteSight was built for Nigerian students: it recognises dishes they actually eat, explains nutrition in terms of the six food groups they learned in school, and suggests fixes using local foods ("add beans or moimoi for protein"), not supplements. It's a final-year project built as a production-style system: auth, consent tracking, admin roles, caching, monitoring and deployment manifests.

## What it does

- **Recognises Nigerian dishes.** A MobileNetV2 classifier over **104 food classes** defined in [`backend/dataset/metadata/nigerian_foods.json`](backend/dataset/metadata/nigerian_foods.json), grouped into carbohydrates, protein, fats & oils, vitamins, minerals and water.
- **Scores the plate.** A rule engine ([`app/core/nutrition_engine.py`](backend/app/core/nutrition_engine.py)) builds a food-group profile, computes a balance score and lists missing groups.
- **Gives feedback that fits.** Admin-editable rules (`nutrition_rules` table) turn gaps into suggestions using local foods.
- **Tracks progress.** Meal history, statistics, trends and weekly insights per student.
- **Privacy by design.** Explicit consent records (data processing / history storage / analytics). History is only kept with consent.
- **Admin roles.** `super_admin`, `admin`, `nutritionist` (manages rules) and `dataset_manager` (manages the food catalogue).
- **Operable.** Health checks, Prometheus metrics, Redis caching (optional; the API degrades gracefully without it), rate limiting and structured logging.

## Architecture

```mermaid
flowchart LR
    M["Expo app<br/>(mobile/)"] -->|"JWT · multipart upload"| API
    W["Web demo<br/>(frontend/index.html)"] --> API
    subgraph API["FastAPI · /api/v1"]
        U["meals/upload"] --> IMG["Image service<br/>validate · resize · thumbnail"]
        IMG --> AI["AI service<br/>MobileNetV2 (PyTorch)"]
        AI --> NE["Nutrition engine<br/>food groups · balance score"]
        NE --> FB["Feedback rules"]
    end
    API --> PG[("PostgreSQL<br/>students · meals · detected_foods<br/>feedback · insights · consent · admin")]
    API -. "cache (optional)" .-> R[("Redis")]
    API --> PR["Prometheus → Grafana"]
```

A meal upload runs end to end in one request. The image is validated (type, size, minimum 224×224, quality score), stored with raw/processed/thumbnail variants, classified, analysed, and the result is saved (`meals` → `detected_foods`). The response includes detected foods, the balance score, missing groups and recommendations.

## Getting started

**Requirements:** Python 3.11, PostgreSQL 15, Node 20+ (mobile app only). Redis is optional.

### 1. Backend

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env            # the backend reads backend/.env
```

Create the database (the default `DATABASE_URL` expects Postgres on port **5433**, matching `docker-compose.yml`):

```bash
createuser -h 127.0.0.1 -p 5433 -s nutrition_user
createdb   -h 127.0.0.1 -p 5433 -O nutrition_user nutrition_feedback
psql -h 127.0.0.1 -p 5433 -U nutrition_user nutrition_feedback -c "ALTER USER nutrition_user PASSWORD 'nutrition_pass';"
alembic upgrade head               # 4 migrations, 13 tables
```

The repo ships **no trained weights**. Create a placeholder model so the AI service can load:

```bash
python scripts/create_mock_model.py --mode mock          # random weights, for development
# or: --mode pretrained  (ImageNet backbone, then fine-tune; see docs/model-training.md)
```

Run it:

```bash
uvicorn app.main:app --reload --port 8000
```

- Health: <http://localhost:8000/health>
- Interactive API docs: <http://localhost:8000/api/v1/docs>

### 2. Web demo (optional)

```bash
cd frontend && python3 -m http.server 3000     # then open http://localhost:3000
```

`BACKEND_CORS_ORIGINS` in `.env` must include `http://localhost:3000` (it does in `.env.example`).

### 3. Mobile app

```bash
cd mobile
npm install
npx expo start          # press i (iOS simulator) or a (Android emulator)
```

The API address is chosen per platform in [`mobile/src/config/environment.ts`](mobile/src/config/environment.ts). The Android emulator uses `10.0.2.2:8000`, iOS uses `127.0.0.1:8000`.

### Docker

```bash
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/create_mock_model.py --mode mock
```

This starts Postgres, Redis, the API and Nginx. Kubernetes manifests (namespace, Postgres, Redis, backend, Nginx, monitoring) live in [`k8s/`](k8s/) with a deploy script. See [docs/deployment.md](docs/deployment.md).

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://nutrition_user:nutrition_pass@127.0.0.1:5433/nutrition_feedback` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379` | Cache (optional) |
| `SECRET_KEY` | placeholder, **change it** | JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `11520` (8 days) | Token lifetime |
| `BACKEND_CORS_ORIGINS` | *(none)* | Comma-separated browser origins |
| `MODEL_PATH` | `models/best_model.pth` | Classifier checkpoint |
| `MAX_UPLOAD_SIZE` | `10485760` | Upload limit in bytes |

## Usage

```bash
API=http://localhost:8000/api/v1

curl -X POST $API/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"ada@unilag.edu.ng","name":"Ada","password":"a-strong-password"}'

TOKEN=$(curl -s -X POST $API/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"ada@unilag.edu.ng","password":"a-strong-password"}' | jq -r .access_token)

curl -X POST $API/consent/ -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"data_processing_consent":true,"history_storage_consent":true}'

curl -X POST $API/meals/upload -H "Authorization: Bearer $TOKEN" -F "file=@lunch.jpg"
```

Upload response (trimmed):

```json
{
  "success": true,
  "meal_id": "b77b9e21-…",
  "validation_results": { "is_valid": true, "quality_score": 0.92, "metadata": { "width": 736, "height": 981 } },
  "ai_analysis": {
    "detected_foods": [ { "food_name": "…", "confidence": 0.85, "food_class": "carbohydrates" } ],
    "nutrition_analysis": {
      "balance_score": 60,
      "present_categories": ["carbohydrates", "protein"],
      "missing_categories": ["vitamins"],
      "recommendations": ["Add vegetables or fruits for vitamins and minerals"]
    },
    "analysis_status": "completed"
  }
}
```

Main route groups: `auth`, `consent`, `meals`, `history` (history, statistics, trends, weekly insights), `insights`, `inference` (direct predict, batch, model status), `nutrition-rules` and `admin`. Full list at `/api/v1/docs`.

## Testing

```bash
cd backend && pytest tests -q
```

34 test files cover models, auth, consent, image handling, inference, the nutrition engine, history/insights and end-to-end flows. Most run on in-memory SQLite. Some integration suites expect Postgres on port 5433.

## Project status

- ✅ The API, database layer, auth, consent, upload/validation pipeline, nutrition engine and history endpoints run end to end (verified locally on Postgres 15).
- ⚠️ **No trained model is published.** With the mock model, no prediction clears the 0.7 confidence threshold, so uploads return clearly labelled **sample results**. Accuracy on real photos is unmeasured.
- ⚠️ `POST /feedback/{meal_id}/generate` is a stub. Feedback currently comes back inline with the upload.
- ⚠️ Some integration tests have harness issues (missing fixtures, a test client not bound to the test DB). Those are known and not product bugs.
- *Unverified:* the Kubernetes manifests and production Nginx config haven't been applied to a cluster as part of this documentation pass.

## Tech stack

**Backend:** Python 3.11 · FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 · PyTorch/torchvision (MobileNetV2) · Pillow/OpenCV · Redis · Prometheus client
**Mobile:** Expo SDK 54 · React Native 0.81 · Expo Router · expo-camera / image-picker
**Infra:** Docker Compose · Kubernetes manifests · Nginx · Prometheus + Grafana

## Further reading

- [Model training](docs/model-training.md): dataset layout, transfer learning (freeze → fine-tune), evaluation
- [Dataset guide](backend/dataset/README.md) and [adding images](backend/dataset/ADDING_IMAGES_GUIDE.md)
- [Testing strategy](docs/testing.md) · [Mobile integration tests](docs/mobile-integration-testing.md) · [Deployment](docs/deployment.md)

## Team

Built by [Enoch (Enochthedev)](https://github.com/Enochthedev) with Inioluwa Adeye.
