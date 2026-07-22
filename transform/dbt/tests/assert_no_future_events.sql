-- Fail if any staged events have timestamps in the future
select event_id, event_timestamp
from {{ ref('stg_events') }}
where event_timestamp > current_timestamp
