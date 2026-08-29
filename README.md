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
