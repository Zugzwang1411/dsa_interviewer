run-backend: cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && ./run_backend.sh
run-frontend: cd frontend && npm install && npm run dev
