-- this sql file is responsible for copying data from staging tables into master tables while ignoring
-- the duplicate entries

-- copy all data from Links into MasterLinks;
INSERT IGNORE {prefix}Links SELECT * FROM {prefix}staging_Links;

-- copy all data from LinksIn into MasterLinks
INSERT IGNORE {prefix}LinksIn SELECT * FROM {prefix}staging_LinksIn;

-- copy all data from LinksPOut into MasterLinksOut
INSERT IGNORE {prefix}LinksOut SELECT * FROM {prefix}staging_LinksOut;
