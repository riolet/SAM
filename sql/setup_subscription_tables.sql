-- Create the Nodes table
CREATE TABLE IF NOT EXISTS s{acct}_Nodes
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,subnet            INT NOT NULL
,alias             VARCHAR(96)
,env               VARCHAR(64)
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,CONSTRAINT PKNodes PRIMARY KEY (ipstart, ipend)
,INDEX nenv (env)
);

-- Create the table of tags
CREATE TABLE IF NOT EXISTS s{acct}_Tags
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,tag               VARCHAR(32)
,CONSTRAINT PKTags PRIMARY KEY (ipstart, ipend, tag)
,CONSTRAINT FKTags FOREIGN KEY (ipstart, ipend) REFERENCES Nodes (ipstart, ipend)
);

-- Create the table for port aliases
CREATE TABLE IF NOT EXISTS s{acct}_PortAliases
(port              INT UNSIGNED NOT NULL
,active            BOOL NOT NULL DEFAULT TRUE
,name              VARCHAR(10) NOT NULL DEFAULT ""
,description       VARCHAR(255) NOT NULL DEFAULT ""
,CONSTRAINT PKPortAliases PRIMARY KEY (port)
);