-- Helper function for debugging
DROP FUNCTION IF EXISTS decodeIP;
CREATE FUNCTION decodeIP (ip INT UNSIGNED)
RETURNS CHAR(15) DETERMINISTIC
RETURN CONCAT(ip DIV 16777216, CONCAT(".", CONCAT(ip DIV 65536 MOD 256, CONCAT(".", CONCAT(ip DIV 256 MOD 256, CONCAT(".", ip MOD 256))))));
SELECT decodeIP(356712447);

-- Create the tables
CREATE TABLE NodesF
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,subnet            INT NOT NULL
,alias             VARCHAR(96)
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,CONSTRAINT PKNodesF PRIMARY KEY (ipstart, ipend)
);

CREATE TABLE LinksA
(src               INT UNSIGNED NOT NULL
,dst               INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinksA PRIMARY KEY (src, dst, port, timestamp)
);

CREATE TABLE LinksB
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinksB PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FKLinksBSrc FOREIGN KEY (src_start, src_end) REFERENCES NodesF (ipstart, ipend)
,CONSTRAINT FKLinksBDst FOREIGN KEY (dst_start, dst_end) REFERENCES NodesF (ipstart, ipend)
);



-- Fill NodesF
INSERT INTO NodesF (ipstart, ipend, subnet, x, y, radius)
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

INSERT INTO NodesF (ipstart, ipend, subnet, x, y, radius)
SELECT twentyfour.__start, twentyfour.__end, 24
    , 0 AS x
    , 0 AS y
    , 20 AS radius
FROM(
    SELECT (ipstart DIV 256 * 256) AS __start
         , (ipstart DIV 256 * 256 + 255) AS __end
    FROM NodesF
    WHERE ipstart = ipend
    GROUP BY __start, __end
) AS twentyfour;

INSERT INTO NodesF (ipstart, ipend, subnet, x, y, radius)
SELECT sixteen.__start, sixteen.__end, 16
    , 0 AS x
    , 0 AS y
    , 200 AS radius
FROM(
    SELECT (ipstart DIV 65536 * 65536) AS __start
         , (ipstart DIV 65536 * 65536 + 65535) AS __end
    FROM NodesF
    WHERE ipstart = ipend
    GROUP BY __start, __end
) AS sixteen;

INSERT INTO NodesF (ipstart, ipend, subnet, x, y, radius)
SELECT eight.__start, eight.__end, 8
    , 0 AS x
    , 0 AS y
    , 2000 AS radius
FROM(
    SELECT (ipstart DIV 16777216 * 16777216) AS __start
         , (ipstart DIV 16777216 * 16777216 + 16777215) AS __end
    FROM NodesF
    WHERE ipstart = ipend
    GROUP BY __start, __end
) AS eight;


-- Fill LinksA
INSERT INTO LinksA (src, dst, port, timestamp, links)
SELECT SourceIP, DestinationIP, DestinationPort
    , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) AS ts
    , COUNT(1) AS links
FROM Syslog
GROUP BY SourceIP, DestinationIP, DestinationPort, ts;


--filter by port
-- columns: address, alias, conns_in, conns_out
SELECT decodeIP(NodesF.ipstart) AS 'address'
    , NodesF.alias AS 'alias'
    , SUM(l_in.links) AS 'Conn IN'
FROM NodesF
LEFT JOIN LinksA AS l_in
    ON l_in.dst BETWEEN NodesF.ipstart AND NodesF.ipend
WHERE NodesF.subnet = 8
GROUP BY NodesF.ipstart, NodesF.alias
LIMIT 10;


-- subnet filter test
SELECT ipstart
    , alias
    ,(SELECT SUM(links)
        FROM LinksA AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn OUT"
    ,(SELECT SUM(links)
        FROM LinksA AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn IN"
FROM NodesF AS nodes
WHERE nodes.subnet = 24
LIMIT 10;
-- port filter test
SELECT ipstart
    , alias
    ,(SELECT SUM(links)
        FROM LinksA AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn OUT"
    ,(SELECT SUM(links)
        FROM LinksA AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn IN"
FROM NodesF AS nodes
WHERE EXISTS (SELECT * FROM LinksA WHERE LinksA.dst BETWEEN nodes.ipstart AND nodes.ipend AND LinksA.port = 443)
LIMIT 10;
-- port AND subnet filter test
SELECT ipstart
    , alias
    ,(SELECT SUM(links)
        FROM LinksA AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn OUT"
    ,(SELECT SUM(links)
        FROM LinksA AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ) AS "Conn IN"
FROM NodesF AS nodes
WHERE nodes.subnet = 24
    && EXISTS (SELECT * FROM LinksA WHERE LinksA.port = 443 && LinksA.dst BETWEEN nodes.ipstart AND nodes.ipend)
LIMIT 10;
-- connections test
SELECT decodeIP(ipstart) AS address
    , alias
    ,COALESCE((SELECT SUM(links)
        FROM LinksA AS l_out
        WHERE l_out.src BETWEEN nodes.ipstart AND nodes.ipend
     ),0) AS "conn_out"
    ,COALESCE((SELECT SUM(links)
        FROM LinksA AS l_in
        WHERE l_in.dst BETWEEN nodes.ipstart AND nodes.ipend
     ),0) AS "conn_in"
FROM NodesF AS nodes
WHERE nodes.subnet = 16
HAVING conn_in < 1
LIMIT 10;



--  IGNORE until later

-- Fill LinksB
CREATE TABLE LinksB
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinksB PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FKLinksBSrc FOREIGN KEY (src_start, src_end) REFERENCES NodesF (ipstart, ipend)
,CONSTRAINT FKLinksBDst FOREIGN KEY (dst_start, dst_end) REFERENCES NodesF (ipstart, ipend)
);
-- adding /32
INSERT INTO LinksB (src_start, src_end, dst_start, dst_end, port, timestamp, links)
SELECT SourceIP AS src_start
    , SourceIP AS src_end
    , DestinationIP AS dst_start
    , DestinationIP AS dst_end
    , DestinationPort
    , SUBSTRING(TIMESTAMPADD(MINUTE, -(MINUTE(Timestamp) MOD 5), Timestamp), 1, 16) AS ts
    , COUNT(1) AS links
FROM Syslog
GROUP BY SourceIP, DestinationIP, DestinationPort, ts;

-- adding /24
















