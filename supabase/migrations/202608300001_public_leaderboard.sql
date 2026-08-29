-- Keep application-owned data private while exposing a read-only leaderboard.
-- The FastAPI backend connects with the database URL and remains responsible
-- for all account, quest, friendship, and score mutations.

alter table if exists public.users enable row level security;
alter table if exists public.sessions enable row level security;
alter table if exists public.daily_quests enable row level security;
alter table if exists public.quest_slots enable row level security;
alter table if exists public.friendships enable row level security;

revoke all on table public.users from anon, authenticated;
revoke all on table public.sessions from anon, authenticated;
revoke all on table public.daily_quests from anon, authenticated;
revoke all on table public.quest_slots from anon, authenticated;
revoke all on table public.friendships from anon, authenticated;

drop view if exists public.public_leaderboard;

create view public.public_leaderboard
with (security_barrier = true)
as
select
    u.id as user_id,
    u.username,
    coalesce(sum(
        case
            when qs.completed is true
             and qs.completed_at >= ((date_trunc('week', now() at time zone 'Asia/Singapore') at time zone 'Asia/Singapore') at time zone 'UTC')
             and qs.completed_at < (((date_trunc('week', now() at time zone 'Asia/Singapore') + interval '7 days') at time zone 'Asia/Singapore') at time zone 'UTC')
            then coalesce((selected.option ->> 'points')::integer, 0)
            else 0
        end
    ), 0)::integer as weekly_gold,
    coalesce(u.daily_streak, 0) as daily_streak
from public.users u
left join public.quest_slots qs on qs.user_id = u.id
left join lateral (
    select option
    from jsonb_array_elements(qs.quest_options::jsonb) option
    where option ->> 'id' = qs.selected_quest_key
    limit 1
) selected on true
group by u.id, u.username, u.daily_streak;

comment on view public.public_leaderboard is
    'Public, read-only weekly leaderboard. It intentionally excludes passwords, sessions, preferences, friendships, locations, and quest history.';

revoke all on table public.public_leaderboard from public;
grant select on table public.public_leaderboard to anon, authenticated;

-- Ensure Supabase REST can discover the new view immediately.
notify pgrst, 'reload schema';
