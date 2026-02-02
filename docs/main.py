from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Enterprise Retail Intelligence System")

# Allow Frontend to talk to Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "R-DIOS Backend Online", "version": "3.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}