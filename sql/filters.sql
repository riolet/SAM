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



-- Fill Nodes
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


-- Fill Links
INSERT INTO Links (src, dst, port, timestamp, links)
SELECT SourceIP, DestinationIP, DestinationPort
    , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) AS ts
    , COUNT(1) AS links
FROM Syslog
GROUP BY SourceIP, DestinationIP, DestinationPort, ts;


-- filter by port
-- columns: address, alias, conns_in, conns_out
SELECT decodeIP(Nodes.ipstart) AS 'address'
    , Nodes.alias AS 'alias'
    , SUM(l_in.links) AS 'Conn IN'
FROM Nodes
LEFT JOIN Links AS l_in
    ON l_in.dst BETWEEN Nodes.ipstart AND Nodes.ipend
WHERE Nodes.subnet = 8
GROUP BY Nodes.ipstart, Nodes.alias
LIMIT 10;


-- subnet filter test
SELECT ipstart
    , alias
    ,(SELECT SUM(links)
        FROM Links AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn OUT"
    ,(SELECT SUM(links)
        FROM Links AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn IN"
FROM Nodes AS nodes
WHERE nodes.subnet = 24
LIMIT 10;
-- port filter test
SELECT ipstart
    , alias
    ,(SELECT SUM(links)
        FROM Links AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn OUT"
    ,(SELECT SUM(links)
        FROM Links AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn IN"
FROM Nodes AS nodes
WHERE EXISTS (SELECT * FROM Links WHERE Links.dst BETWEEN nodes.ipstart AND nodes.ipend AND Links.port = 443)
LIMIT 10;
-- port AND subnet filter test
SELECT ipstart
    , alias
    ,(SELECT SUM(links)
        FROM Links AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn OUT"
    ,(SELECT SUM(links)
        FROM Links AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn IN"
FROM Nodes AS nodes
WHERE nodes.subnet = 24
    && EXISTS (SELECT * FROM Links WHERE Links.port = 443 && Links.dst BETWEEN nodes.ipstart AND nodes.ipend)
LIMIT 10;
-- connections test
SELECT decodeIP(ipstart) AS address
    , alias
    ,COALESCE((SELECT SUM(links)
        FROM Links AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ),0) AS "conn_out"
    ,COALESCE((SELECT SUM(links)
        FROM Links AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ),0) AS "conn_in"
FROM Nodes AS nodes
WHERE nodes.subnet = 16
HAVING conn_in < 1
LIMIT 10;



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













