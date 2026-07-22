-- Bronze events staged for transform
-- Source: storage/iceberg/tables/bronze_events (future Iceberg source)

select
    cast(id as varchar) as event_id,
    cast(event_type as varchar) as event_type,
    cast(event_timestamp as timestamp) as event_timestamp,
    cast(user_id as varchar) as user_id,
    cast(payload as varchar) as payload_raw,
    date(cast(event_timestamp as timestamp)) as event_date
from {{ source('bronze', 'events') }}
