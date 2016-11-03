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
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,CONSTRAINT PKNodes PRIMARY KEY (ipstart, ipend)
);

-- Create the Links table
CREATE TABLE IF NOT EXISTS Links
(src               INT UNSIGNED NOT NULL
,dst               INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinks PRIMARY KEY (src, dst, port, timestamp)
);

CREATE TABLE IF NOT EXISTS LinksIn
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinksIn PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FKLinksInSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FKLinksInDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);

CREATE TABLE IF NOT EXISTS LinksOut
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinksOut PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FKLinksOutSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FKLinksOutDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);
