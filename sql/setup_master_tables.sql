-- this sql file is resposible for creating all master tables if they do not exist yet

-- Create MasterNodes table if it doesn't exist
CREATE TABLE IF NOT EXISTS MasterNodes LIKE Nodes;

-- Create MasterLinks table if it doesn't exist
CREATE TABLE IF NOT EXISTS MasterLinks LIKE Links;

-- Create MasterLinksIn table if it doesn't exist
CREATE TABLE IF NOT EXISTS MasterLinksIn LIKE LinksIn;

-- Create MasterLinksOut table if it doesn't exist
CREATE TABLE IF NOT EXISTS MasterLinksOut LIKE LinksOut;

-- Create MasterTags table if it doesn't exist
CREATE TABLE IF NOT EXISTS MasterTags LIKE Tags;

-- Create MasterSyslog table if it doesn't exist
CREATE TABLE IF NOT EXISTS MasterSyslog LIKE Syslog;



