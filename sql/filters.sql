-- Helper function for debugging
DROP FUNCTION IF EXISTS decodeIP;
CREATE FUNCTION decodeIP (ip INT UNSIGNED)
RETURNS CHAR(15) DETERMINISTIC
RETURN CONCAT(ip DIV 16777216, CONCAT(".", CONCAT(ip DIV 65536 MOD 256, CONCAT(".", CONCAT(ip DIV 256 MOD 256, CONCAT(".", ip MOD 256))))));
SELECT decodeIP(356712447);

-- Create the tables
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



-- ======================================================
-- Fill Nodes
-- ======================================================
INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT log.ip, log.ip, 32
    , 0 AS x
    , 0 AS y
    , 2 AS radius
FROM(
    SELECT SourceIP AS ip
    FROM Syslog
    UNION
    SELECT DestinationIP AS ip
    FROM Syslog
) AS log;

INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT twentyfour.__start, twentyfour.__end, 24
    , 0 AS x
    , 0 AS y
    , 20 AS radius
FROM(
    SELECT (ipstart DIV 256 * 256) AS __start
         , (ipstart DIV 256 * 256 + 255) AS __end
    FROM Nodes
    WHERE ipstart = ipend
    GROUP BY __start, __end
) AS twentyfour;

INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT sixteen.__start, sixteen.__end, 16
    , 0 AS x
    , 0 AS y
    , 200 AS radius
FROM(
    SELECT (ipstart DIV 65536 * 65536) AS __start
         , (ipstart DIV 65536 * 65536 + 65535) AS __end
    FROM Nodes
    WHERE ipstart = ipend
    GROUP BY __start, __end
) AS sixteen;

INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT eight.__start, eight.__end, 8
    , 0 AS x
    , 0 AS y
    , 2000 AS radius
FROM(
    SELECT (ipstart DIV 16777216 * 16777216) AS __start
         , (ipstart DIV 16777216 * 16777216 + 16777215) AS __end
    FROM Nodes
    WHERE ipstart = ipend
    GROUP BY __start, __end
) AS eight;



INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT (log.ip * 16777216) AS 'ipstart'
    , ((log.ip + 1) * 16777216 - 1) AS 'ipend'
    , 8 AS 'subnet'
    , (331776 * (log.ip % 16) / 7.5 - 331776) AS 'x'
    , (331776 * (log.ip DIV 16) / 7.5 - 331776) AS 'y'
    , 20736 AS 'radius'
FROM(
    SELECT SourceIP DIV 16777216 AS 'ip'
    FROM Syslog
    UNION
    SELECT DestinationIP DIV 16777216 AS 'ip'
    FROM Syslog
) AS log;

INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT (log.ip * 65536) AS 'ipstart'
    , ((log.ip + 1) * 65536 - 1) AS 'ipend'
    , 16 AS 'subnet'
    , ((parent.radius * (log.ip MOD 16) / 7.5 - parent.radius) + parent.x) AS 'x'
    , ((parent.radius * (log.ip MOD 256 DIV 16) / 7.5 - parent.radius) + parent.y) AS 'y'
    , (parent.radius / 24) AS 'radius'
FROM(
    SELECT SourceIP DIV 65536 AS 'ip'
    FROM Syslog
    UNION
    SELECT DestinationIP DIV 65536 AS 'ip'
    FROM Syslog
) AS log
JOIN Nodes AS parent
    ON parent.subnet=8 && parent.ipstart = (log.ip DIV 256 * 16777216);

INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT (log.ip * 256) AS 'ipstart'
    , ((log.ip + 1) * 256 - 1) AS 'ipend'
    , 24 AS 'subnet'
    , ((parent.radius * (log.ip MOD 16) / 7.5 - parent.radius) + parent.x) AS 'x'
    , ((parent.radius * (log.ip MOD 256 DIV 16) / 7.5 - parent.radius) + parent.y) AS 'y'
    , (parent.radius / 24) AS 'radius'
FROM(
    SELECT SourceIP DIV 256 AS 'ip'
    FROM Syslog
    UNION
    SELECT DestinationIP DIV 256 AS 'ip'
    FROM Syslog
) AS log
JOIN Nodes AS parent
    ON parent.subnet=16 && parent.ipstart = (log.ip DIV 256 * 65536);

INSERT INTO Nodes (ipstart, ipend, subnet, x, y, radius)
SELECT log.ip AS 'ipstart'
    , log.ip AS 'ipend'
    , 32 AS 'subnet'
    , ((parent.radius * (log.ip MOD 16) / 7.5 - parent.radius) + parent.x) AS 'x'
    , ((parent.radius * (log.ip MOD 256 DIV 16) / 7.5 - parent.radius) + parent.y) AS 'y'
    , (parent.radius / 24) AS 'radius'
FROM(
    SELECT SourceIP AS 'ip'
    FROM Syslog
    UNION
    SELECT DestinationIP AS 'ip'
    FROM Syslog
) AS log
JOIN Nodes AS parent
    ON parent.subnet=24 && parent.ipstart = (log.ip DIV 256 * 256);


-- ======================================================
-- Fill Links
-- ======================================================
INSERT INTO Links (src, dst, port, timestamp, links)
SELECT SourceIP, DestinationIP, DestinationPort
    , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) AS ts
    , COUNT(1) AS links
FROM Syslog
GROUP BY SourceIP, DestinationIP, DestinationPort, ts;

-- LinksIn and Out
-- adding /8
INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src DIV 16777216 * 16777216 AS 'src_start'
    , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
    , dst DIV 16777216 * 16777216 AS 'dst_start'
    , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;

INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src_start, src_end, dst_start, dst_end, port, timestamp, links
FROM LinksIn;

-- adding /16
INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src DIV 65536 * 65536 AS 'src_start'
    , src DIV 65536 * 65536 + 65535 AS 'src_end'
    , dst DIV 65536 * 65536 AS 'dst_start'
    , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) = (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 16777216 * 16777216 AS 'src_start'
    , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
    , dst DIV 65536 * 65536 AS 'dst_start'
    , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) != (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;

INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src DIV 65536 * 65536 AS 'src_start'
    , src DIV 65536 * 65536 + 65535 AS 'src_end'
    , dst DIV 65536 * 65536 AS 'dst_start'
    , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) = (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 65536 * 65536 AS 'src_start'
    , src DIV 65536 * 65536 + 65535 AS 'src_end'
    , dst DIV 16777216 * 16777216 AS 'dst_start'
    , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) != (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;


-- adding /24
INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src DIV 256 * 256 AS 'src_start'
    , src DIV 256 * 256 + 255 AS 'src_end'
    , dst DIV 256 * 256 AS 'dst_start'
    , dst DIV 256 * 256 + 255 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 65536) = (dst DIV 65536)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 65536 * 65536 AS 'src_start'
    , src DIV 65536 * 65536 + 65535 AS 'src_end'
    , dst DIV 256 * 256 AS 'dst_start'
    , dst DIV 256 * 256 + 255 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) = (dst DIV 16777216)
  AND (src DIV 65536) != (dst DIV 65536)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 16777216 * 16777216 AS 'src_start'
    , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
    , dst DIV 256 * 256 AS 'dst_start'
    , dst DIV 256 * 256 + 255 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) != (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;


INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src DIV 256 * 256 AS 'src_start'
    , src DIV 256 * 256 + 255 AS 'src_end'
    , dst DIV 256 * 256 AS 'dst_start'
    , dst DIV 256 * 256 + 255 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 65536) = (dst DIV 65536)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 256 * 256 AS 'src_start'
    , src DIV 256 * 256 + 255 AS 'src_end'
    , dst DIV 65536 * 65536 AS 'dst_start'
    , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) = (dst DIV 16777216)
  AND (src DIV 65536) != (dst DIV 65536)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 256 * 256 AS 'src_start'
    , src DIV 256 * 256 + 255 AS 'src_end'
    , dst DIV 16777216 * 16777216 AS 'dst_start'
    , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) != (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;

-- adding /32
INSERT INTO LinksIn (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src AS 'src_start'
    , src AS 'src_end'
    , dst AS 'dst_start'
    , dst AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 256) = (dst DIV 256)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 256 * 256 AS 'src_start'
    , src DIV 256 * 256 + 255 AS 'src_end'
    , dst AS 'dst_start'
    , dst AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 65536) = (dst DIV 65536)
  AND (src DIV 256) != (dst DIV 256)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 65536 * 65536 AS 'src_start'
    , src DIV 65536 * 65536 + 65535 AS 'src_end'
    , dst AS 'dst_start'
    , dst AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) = (dst DIV 16777216)
  AND (src DIV 65536) != (dst DIV 65536)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src DIV 16777216 * 16777216 AS 'src_start'
    , src DIV 16777216 * 16777216 + 16777215 AS 'src_end'
    , dst AS 'dst_start'
    , dst AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) != (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;


INSERT INTO LinksOut (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT src AS 'src_start'
    , src AS 'src_end'
    , dst AS 'dst_start'
    , dst AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 256) = (dst DIV 256)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src AS 'src_start'
    , src AS 'src_end'
    , dst DIV 256 * 256 AS 'dst_start'
    , dst DIV 256 * 256 + 255 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 65536) = (dst DIV 65536)
  AND (src DIV 256) != (dst DIV 256)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src AS 'src_start'
    , src AS 'src_end'
    , dst DIV 65536 * 65536 AS 'dst_start'
    , dst DIV 65536 * 65536 + 65535 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) = (dst DIV 16777216)
  AND (src DIV 65536) != (dst DIV 65536)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp
UNION
SELECT src AS 'src_start'
    , src AS 'src_end'
    , dst DIV 16777216 * 16777216 AS 'dst_start'
    , dst DIV 16777216 * 16777216 + 16777215 AS 'dst_end'
    , port
    , timestamp
    , SUM(links)
FROM Links
WHERE (src DIV 16777216) != (dst DIV 16777216)
GROUP BY src_start, src_end, dst_start, dst_end, port, timestamp;


-- TESTING
SELECT src AS 'ip', port AS 'port', sum(links) AS 'links'
FROM Links
WHERE dst BETWEEN 3170893824 AND 3187671039
 && Timestamp BETWEEN FROM_UNIXTIME(1466554050) AND FROM_UNIXTIME(1466557649)
GROUP BY src, port
ORDER BY links DESC
LIMIT 50;
-- 50 rows, 0.13s

SELECT temp.port, links
FROM
    (SELECT DestinationPort AS port, COUNT(*) AS links
    FROM Syslog
    WHERE DestinationIP >= 3170893824 && DestinationIP <= 3187671039
         && Timestamp BETWEEN FROM_UNIXTIME(1466554050) AND FROM_UNIXTIME(1466557649)
    GROUP BY port
    ) AS temp
ORDER BY links DESC
LIMIT 50;
-- 20 rows, 0.08s
SELECT port AS 'port', sum(links) AS 'links'
FROM Links
WHERE dst BETWEEN 3170893824 AND 3187671039
 && Timestamp BETWEEN FROM_UNIXTIME(1466554050) AND FROM_UNIXTIME(1466557649)
GROUP BY port
ORDER BY links DESC
LIMIT 50;





