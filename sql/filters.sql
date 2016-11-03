-- ======================================================
-- Fill Nodes
-- ======================================================
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


-- adding /16




-- adding /24



-- adding /32






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


SELECT dst AS 'Address', COUNT(DISTINCT port) AS 'Ports', COUNT(links) AS 'Connections'
FROM Links
GROUP BY Address
ORDER BY Ports DESC, Connections DESC
LIMIT 100;