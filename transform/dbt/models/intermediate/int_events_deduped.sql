-- Deduplicate bronze events by event_id (latest timestamp wins)
with ranked as (
    select
        *,
        row_number() over (
            partition by event_id
            order by event_timestamp desc
        ) as _row_num
    from {{ ref('stg_events') }}
)

select
    event_id,
    event_type,
    event_timestamp,
    user_id,
    payload_raw,
    event_date
from ranked
where _row_num = 1
