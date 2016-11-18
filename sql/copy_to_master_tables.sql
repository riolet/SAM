-- append data from staging tables into master tables

INSERT MasterNodes SELECT * FROM Nodes;

INSERT MasterLinks SELECT * FROM Links;

INSERT MasterLinksIn SELECT * FROM LinksIn;

INSERT MasterLinksOut SELECT * FROM LinksOut;

--INSERT MasterTags SELECT * From Tags;