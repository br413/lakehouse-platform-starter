{{
    config(
        materialized="incremental",
        unique_key=["event_date", "event_type"],
        incremental_strategy="delete+insert",
    )
}}

select
    event_date,
    event_type,
    count(*) as event_count,
    count(distinct user_id) as unique_users
from {{ ref('int_events_deduped') }}
{% if is_incremental() %}
    where event_date >= (select coalesce(max(event_date), '1900-01-01') from {{ this }})
{% endif %}
group by 1, 2
