-- copy data from staging tables into master tables

INSERT IGNORE MasterNodes SELECT * FROM Nodes;

INSERT IGNORE MasterLinks SELECT * FROM Links;

INSERT IGNORE MasterLinksIn SELECT * FROM LinksIn;

INSERT IGNORE MasterLinksOut SELECT * FROM LinksOut;

INSERT IGNORE MasterTags SELECT * From Tags;

INSERT IGNORE MasterSyslog SELECT * From Syslog;