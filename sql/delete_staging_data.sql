-- this sql file is responsible for deleting all data from staging tables

DELETE FROM s{acct}_ds{id}_StagingLinks;
DELETE FROM s{acct}_ds{id}_Syslog;
