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
,CONSTRAINT PK{acct}Nodes PRIMARY KEY (ipstart, ipend)
,INDEX nenv (env)
);


-- Create the table of tags
CREATE TABLE IF NOT EXISTS s{acct}_Tags
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,tag               VARCHAR(32)
,CONSTRAINT PK{acct}Tags PRIMARY KEY (ipstart, ipend, tag)
,CONSTRAINT FK{acct}Tags FOREIGN KEY (ipstart, ipend) REFERENCES s{acct}_Nodes (ipstart, ipend)
);

-- Create the table for port aliases
CREATE TABLE IF NOT EXISTS s{acct}_PortAliases
(port              INT UNSIGNED NOT NULL
,protocols         TEXT
,active            BOOL NOT NULL DEFAULT TRUE
,name              VARCHAR(10) NOT NULL DEFAULT ""
,description       VARCHAR(255) NOT NULL DEFAULT ""
,CONSTRAINT PK{acct}PortAliases PRIMARY KEY (port)
);

-- Create the table for security rules (params)
CREATE TABLE IF NOT EXISTS s{acct}_Rules
(id                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
,rule_path         VARCHAR(256) NOT NULL
,active            BOOL NOT NULL
,name              VARCHAR(64) NOT NULL
,description       TEXT NOT NULL
,params            TEXT NOT NULL
);

-- Create the table for security alerts
CREATE TABLE IF NOT EXISTS s{acct}_Alerts
(id                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
,ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,log_time          INT UNSIGNED NOT NULL
,report_time       INT UNSIGNED NOT NULL
,severity          TINYINT(1) NOT NULL
,viewed            TINYINT(1) NOT NULL DEFAULT 0
,label             VARCHAR(32) NOT NULL
,rule_id           INT UNSIGNED
,rule_name         VARCHAR(64)
,details           TEXT
);

-- Create the table for Anomaly Detection
CREATE TABLE IF NOT EXISTS s{acct}_ADWarnings
(id                INT UNSIGNED NOT NULL PRIMARY KEY
,host              INT UNSIGNED NOT NULL
,log_time          INT UNSIGNED NOT NULL
,reason            TEXT NOT NULL
,status            VARCHAR(32) NOT NULL
,details           TEXT
);
