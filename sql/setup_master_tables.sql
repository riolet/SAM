-- Create MasterNodes table
CREATE TABLE IF NOT EXISTS MasterNodes LIKE Nodes;

-- Create MasterLinks table
CREATE TABLE IF NOT EXISTS MasterLinks LIKE Links;

-- Create MasterLinksIn table
CREATE TABLE IF NOT EXISTS MasterLinksIn LIKE LinksIn;

-- Create MasterLinksOut table
CREATE TABLE IF NOT EXISTS MasterLinksOut LIKE LinksOut;

-- Create MasterTags table
CREATE TABLE IF NOT EXISTS MasterTags LIKE Tags;

-- Create MasterSyslog table
CREATE TABLE IF NOT EXISTS MasterSyslog LIKE Syslog;



