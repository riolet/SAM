-- Create the MasterNodes table
CREATE TABLE IF NOT EXISTS MasterNodes LIKE Nodes;

-- Create the MasterLinks table
CREATE TABLE IF NOT EXISTS MasterLinks LIKE Links;

-- Create the MasterLinksIn table
CREATE TABLE IF NOT EXISTS MasterLinksIn LIKE LinksIn;

-- Create the MasterLinksOut table
CREATE TABLE IF NOT EXISTS MasterLinksOut LIKE LinksOut;

-- Create the table of tags
CREATE TABLE IF NOT EXISTS Tags
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,tag               VARCHAR(32)
,CONSTRAINT PKTags PRIMARY KEY (ipstart, ipend, tag)
,CONSTRAINT FKTags FOREIGN KEY (ipstart, ipend) REFERENCES MasterNodes (ipstart, ipend)
);

