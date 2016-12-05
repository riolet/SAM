-- this sql file is responsible for copying data from staging tables into master tables while ignoring
-- the duplicate entries

-- copy all data from Nodes to MasterNodes
INSERT IGNORE MasterNodes SELECT * FROM Nodes;

-- copy all data from Links into MasterLinks;
INSERT IGNORE MasterLinks SELECT * FROM Links;

-- copy all data from LinksIn into MasterLinks
INSERT IGNORE MasterLinksIn SELECT * FROM LinksIn;

-- copy all data from LinksPOut into MasterLinksOut
INSERT IGNORE MasterLinksOut SELECT * FROM LinksOut;

-- copy all data from Tags into MasterTags
INSERT IGNORE MasterTags SELECT * From Tags;

-- copy all data from Syslog into MasterSyslog
INSERT IGNORE MasterSyslog SELECT * From Syslog;