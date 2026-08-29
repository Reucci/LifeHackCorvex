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
