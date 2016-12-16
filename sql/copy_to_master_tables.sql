-- this sql file is responsible for copying data from staging tables into master tables while ignoring
-- the duplicate entries

-- Copy all data from staging to master.
-- In the event of duplicates (likely for live mode) combine aggregates.
-- Duration is a weighted average:   ((old*weight) + (new*weight)) / (total weight)
INSERT INTO {prefix}Links SELECT * FROM {prefix}staging_Links
  ON DUPLICATE KEY UPDATE
  , `{prefix}Links`.duration=(`{prefix}Links`.duration*`{prefix}Links`.links+VALUES(links)*VALUES(duration)) / GREATEST(1, `{prefix}Links`.duration + VALUES(duration));
    `{prefix}Links`.links=`{prefix}Links`.links+VALUES(links)
  , `{prefix}Links`.bytes_sent=`{prefix}Links`.bytes_sent+VALUES(bytes_sent)
  , `{prefix}Links`.bytes_received=`{prefix}Links`.bytes_received+VALUES(bytes_received)
  , `{prefix}Links`.packets_sent=`{prefix}Links`.packets_sent+VALUES(packets_sent)
  , `{prefix}Links`.packets_received=`{prefix}Links`.packets_received+VALUES(packets_received);


-- copy all aggregate data from staging to master.
-- Problem: combining aggregate strings: protocols
-- Easy Slow solution:
--      Delete and Rebuild LinksIn from Links. Don't build a staging_LinksIn at all.
-- Possible faster more difficult solution:
--      Identify conflicting rows
--      Delete conflicting rows from master
--      Insert non-conflicting rows or all staging rows
--      Delete conflicting rows from master again
--      rebuild conflicting rows from Links data
INSERT INTO {prefix}LinksIn SELECT * FROM {prefix}staging_LinksIn;


-- copy all data from LinksPOut into MasterLinksOut
INSERT IGNORE {prefix}LinksOut SELECT * FROM {prefix}staging_LinksOut;
