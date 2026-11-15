# UPI Offline Mesh — Full-stack React + FastAPI

## Structure
- `frontend/`: React + Vite dashboard
- `backend/`: FastAPI service, SQLAlchemy database, encryption, mesh simulator

## Run backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Run frontend (new terminal)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Open http://localhost:5173.

The backend CORS policy allows the local Vite origin `http://localhost:5173`. For deployment, change it to your actual frontend origin or serve the built React app through Nginx on the same origin.

## Build frontend for deployment
```bash
cd frontend
npm run build
```
Vite writes the production bundle to `frontend/dist/`.

## Important
This is a learning simulation. It does not connect to NPCI, banks, or real UPI rails. The mesh is simulated rather than Bluetooth transport. Never enter a real UPI PIN.
