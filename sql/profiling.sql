-- DEMO for how to get profiling information from MySQL

-- 1. Ensure that statement and stage instrumentation is enabled by updating the setup_instruments table.
-- Some instruments may already be enabled by default.
UPDATE performance_schema.setup_instruments SET ENABLED = 'YES', TIMED = 'YES'
  WHERE NAME LIKE '%statement/%';
UPDATE performance_schema.setup_instruments SET ENABLED = 'YES', TIMED = 'YES'
  WHERE NAME LIKE '%stage/%';

-- 2. Ensure that events_statements_* and events_stages_* consumers are enabled.
-- Some consumers may already be enabled by default.
UPDATE performance_schema.setup_consumers SET ENABLED = 'YES'
  WHERE NAME LIKE '%events_statements_%';

UPDATE performance_schema.setup_consumers SET ENABLED = 'YES'
  WHERE NAME LIKE '%events_stages_%';

-- 3. Run the statement that you want to profile.
SELECT * FROM Nodes WHERE 123456789 BETWEEN ipstart AND ipend;

-- 4. Find the matching event_id in the history by searching for part of the query string
SELECT EVENT_ID, TRUNCATE(TIMER_WAIT/1000000000000,6) as Duration, SQL_TEXT
  FROM performance_schema.events_statements_history_long
  WHERE SQL_TEXT like '%LIMIT 50;';

-- 5. Check out the detailed view to see stages by using the EVENT_ID from step 4.
SELECT event_name AS Stage, TRUNCATE(TIMER_WAIT/1000000000000,6) AS Duration
  FROM performance_schema.events_stages_history_long
  WHERE NESTING_EVENT_ID=31;