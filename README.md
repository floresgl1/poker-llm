# poker-llm

A Texas Hold'em engine for benchmarking LLMs against each other, with a FastAPI
backend and a React dashboard for reviewing results.

## Layout

```
.
├── main.py                  FastAPI app serving the dashboard API
├── demo.py                  Runnable demos (comparison, tournament, round-robin)
├── requirements.txt
│
├── engine/                  Core poker rules
│   ├── poker_state.py       GameState / Player
│   ├── deck.py
│   ├── hand_evaluator.py
│   └── action_handler.py
│
├── game_management/         Orchestration
│   ├── game_config.py
│   ├── game_runner.py       Single-hand driver
│   ├── table.py             Multi-hand session
│   ├── tournament.py        Knockout play with escalating blinds
│   └── model_comparison.py  A/B and round-robin benchmarking
│
├── llm_integration/
│   ├── llm_interface.py     Abstract player interface
│   ├── llm_models.py        Claude / GPT-4 / Random / CallAny adapters
│   └── prompt_builder.py    Strategic prompt construction
│
├── evaluation/              Metrics & logging helpers (planned, see docs/PROGRESS.md)
├── tests/                   pytest suite
├── docs/                    Progress notes and implementation summaries
│
└── frontend/                Vite + React + TypeScript dashboard
    ├── index.html
    ├── vite.config.ts       Defines the `@/` -> `src/` alias
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── views/Dashboard.tsx
        ├── components/dashboard/   Charts, hand list, hand viewer
        ├── services/api.ts         Backend client
        ├── types/poker.ts          Shared API types
        └── styles/Dashboard.css
```

## Running

Backend (serves on `http://127.0.0.1:8000`):

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend (serves on `http://localhost:5173`, the origin the backend allows via CORS):

```bash
cd frontend
npm install
npm run dev
```

Tests and demos:

```bash
python -m pytest tests/ -q
python demo.py
```

## Notes

- `evaluation/` was previously named `logging/`, which shadowed Python's standard
  library `logging` module that six modules import. Do not rename it back.
- The API reads `comparison_results.json` and `tournament_results.json` from the
  working directory. These are generated artifacts and are gitignored — produce
  them by running a comparison or tournament first.
- The dashboard components import `@/components/ui/button` and
  `@/components/ui/dialog` (shadcn/ui). Those are not vendored yet; install them
  with `npx shadcn@latest add button dialog` before building the frontend.
