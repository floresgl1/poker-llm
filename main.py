import json
from pathlib import Path
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CORS Configuration ---
# This allows your React frontend (running on http://localhost:5173)
# to make requests to this backend.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/leaderboard")
async def get_leaderboard():
    """
    Reads and returns the model comparison results from the generated JSON file.
    """
    results_path = Path("comparison_results.json")
    if not results_path.exists():
        raise HTTPException(status_code=404, detail="Comparison results not found. Please run a model comparison first.")
    
    with open(results_path, "r") as f:
        data = json.load(f)
    
    # The frontend expects a 'title' and 'models' structure.
    # Let's adapt the backend output to match it.
    return {
        "title": "Model Comparison Leaderboard",
        "models": data.get("leaderboard", [])
    }


@app.get("/tournament")
async def get_tournament_results():
    """
    Reads and returns the tournament results from the generated JSON file.
    """
    results_path = Path("tournament_results.json")
    if not results_path.exists():
        raise HTTPException(status_code=404, detail="Tournament results not found. Please run a tournament first.")
    
    with open(results_path, "r") as f:
        data = json.load(f)
    
    # Adapt the backend output to match the frontend's expected structure.
    return {
        "title": "Live Tournament Dashboard",
        "players": data.get("final_results", []),
        "hands_played": data.get("hands_played", 0),
        "current_blind_level": data.get("final_blind_level", 1),
        "blinds": data.get("current_blinds", [0, 0]),
        "eliminations": data.get("eliminations", [])
    }


HAND_HISTORY_DIR = Path("hand_histories")

@app.get("/hands")
async def list_hand_histories(page: int = 1, limit: int = 15):
    """
    Lists available hand history files with pagination.
    """
    if not HAND_HISTORY_DIR.exists():
        # Create the directory if it doesn't exist to avoid errors on first run
        HAND_HISTORY_DIR.mkdir(exist_ok=True)
        return {"hands": [], "total": 0, "page": 1, "limit": limit}
    
    # Sort files by modification time, newest first
    try:
        files = sorted(HAND_HISTORY_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)
        total_hands = len(files)

        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_files = files[start_index:end_index]

        hands_data = [{"hand_id": f.stem, "timestamp": os.path.getmtime(f)} for f in paginated_files]

        return {"hands": hands_data, "total": total_hands, "page": page, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading hand histories: {e}")

@app.get("/hands/{hand_id}")
async def get_hand_history(hand_id: str):
    """
    Retrieves the data for a single hand history.
    """
    hand_file = HAND_HISTORY_DIR / f"{hand_id}.json"
    if not hand_file.exists():
        raise HTTPException(status_code=404, detail="Hand history not found.")
    
    with open(hand_file, "r") as f:
        return json.load(f)