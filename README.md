# LifeHackCorvex

## Supabase database

The backend can use Supabase Postgres through `ECOLINGS_DATABASE_URL`. Copy
`.env.example` to `.env`, fill in the pooled Supabase connection string, and
start the API from the `backend` directory. `.env` files are ignored by Git.

Run `python backend/apply_migrations.py` to create the application tables and
apply every checked-in Supabase migration. The migration keeps all application
tables private and exposes only the read-only `public_leaderboard` view to
Supabase's `anon` role.

Public clients may read the leaderboard through:

```text
GET https://<project-ref>.supabase.co/rest/v1/public_leaderboard
    ?select=user_id,username,weekly_gold,daily_streak
    &order=weekly_gold.desc,daily_streak.desc,username.asc
```

Send the project's publishable anon key in both the `apikey` and
`Authorization: Bearer <anon-key>` headers. Never put the database password or
service-role key in frontend code.

## Public deployment

`render.yaml` deploys the FastAPI backend and React frontend as two linked
Render services. Create a Render Blueprint from this repository and provide
`ECOLINGS_DATABASE_URL` when prompted. The frontend is configured to call the
public backend, and both services redeploy automatically from `main`.

For local frontend development against the public backend, copy
`frontend/.env.example` to `frontend/.env.local` before running `npm start`.
The deployed API accepts requests from the production site and local React
development servers on ports 3000 and 5173.

## Optional OpenAI features

EcoLings uses the OpenAI Responses API only from the FastAPI backend. When no
`OPENAI_API_KEY` is configured, deterministic weather quests, local dialogue,
and manual photo confirmation continue to work.

To enable AI-generated weather quest variants, personalized Ecoling dialogue,
and moderated photo verification:

1. Copy `backend/.env.example` to `backend/.env` for local development.
2. Set `OPENAI_API_KEY` in that untracked file. Never put the key in React.
3. On Render, set the secret `OPENAI_API_KEY` environment variable on the API
   service. The Blueprint already declares the remaining safe defaults.
4. Keep an authoritative project budget in the OpenAI dashboard. The
   `OPENAI_DAILY_BUDGET_USD` setting is an additional in-process guard and
   resets if the service restarts.

Authenticated users can inspect feature availability and today's estimated
in-process spend at `GET /ai/status`.

### Bulk quest library generation

Prepare 500 discounted Batch API requests without spending anything:

```powershell
cd backend
venv\Scripts\python.exe scripts\openai_quest_batch.py prepare --requests 500
```

Review `artifacts/openai/weather-quest-batch.jsonl`, then explicitly submit it:

```powershell
venv\Scripts\python.exe scripts\openai_quest_batch.py submit --confirm-spend
```

Use the returned batch ID with the `status` and `download` commands. Screen the
downloaded candidates before human review:

```powershell
venv\Scripts\python.exe scripts\review_openai_quests.py
```

Generated artifacts are ignored by Git. No generated quest is automatically
promoted into the permanent deterministic catalogue.
