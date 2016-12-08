-- this sql file is responsible for deleting all data from staging tables

-- delete all data from LinksIn table
DELETE FROM {prefix}staging_LinksIn;

-- delete all data from LinksOut table
DELETE FROM {prefix}staging_LinksOut;

-- delete all data from Links table
DELETE FROM {prefix}staging_Links;

-- delete all data from Syslog table
DELETE FROM {prefix}Syslog;
