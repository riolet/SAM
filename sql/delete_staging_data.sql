-- this sql file is responsible for deleting all data from staging tables

-- delete all data from LinksIn table
DELETE FROM LinksIn;

-- delete all data from LinksOut table
DELETE FROM LinksOut;

-- delete all data from Links table
DELETE FROM Links;

-- delete all data from Tags table
DELETE FROM Tags;

-- delete all data from Nodes table
DELETE FROM Nodes;

-- delete all data from Syslog table
DELETE FROM Syslog;
