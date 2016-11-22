-- Translates an IP from 1234567890 to "73.150.2.210"
DROP FUNCTION IF EXISTS decodeIP;
CREATE FUNCTION decodeIP (ip INT UNSIGNED)
RETURNS CHAR(15) DETERMINISTIC
RETURN CONCAT(ip DIV 16777216, CONCAT(".", CONCAT(ip DIV 65536 MOD 256, CONCAT(".", CONCAT(ip DIV 256 MOD 256, CONCAT(".", ip MOD 256))))));
SELECT decodeIP(356712447);

-- Create the Nodes table
CREATE TABLE IF NOT EXISTS Nodes
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

-- Create the Links table
CREATE TABLE IF NOT EXISTS Links
(src               INT UNSIGNED NOT NULL
,dst               INT UNSIGNED NOT NULL
,port              INT NOT NULL
,protocol          CHAR(8) NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1 NOT NULL
,bytes_sent        INT NOT NULL
,bytes_received    INT
,packets_sent      INT NOT NULL
,packets_received  INT
,duration          INT NOT NULL
,CONSTRAINT PKLinks PRIMARY KEY (src, dst, port, protocol, timestamp)
);

CREATE TABLE IF NOT EXISTS LinksIn
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,protocols         VARCHAR(1024)
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,bytes             INT NOT NULL
,packets           INT NOT NULL
,CONSTRAINT PKLinksIn PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FKLinksInSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FKLinksInDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);

CREATE TABLE IF NOT EXISTS LinksOut
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,protocols         VARCHAR(1024)
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,bytes             INT NOT NULL
,packets           INT NOT NULL
,CONSTRAINT PKLinksOut PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FKLinksOutSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FKLinksOutDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);

-- Create the table of tags
CREATE TABLE IF NOT EXISTS Tags
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,tag               VARCHAR(32)
,CONSTRAINT PKTags PRIMARY KEY (ipstart, ipend, tag)
,CONSTRAINT FKTags FOREIGN KEY (ipstart, ipend) REFERENCES Nodes (ipstart, ipend)
);
