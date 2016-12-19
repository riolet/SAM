-- this sql file is responsible for deleting all data from staging tables

-- delete all data from Links table
DELETE FROM {prefix}staging_Links;

-- delete all data from Syslog table
DELETE FROM {prefix}Syslog;
