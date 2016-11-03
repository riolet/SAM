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


SELECT CONCAT(decodeIP(ipstart), CONCAT('/', subnet)) AS address
    , alias
    ,COALESCE((SELECT SUM(links)
        FROM LinksOut AS l_out
        WHERE l_out.src_start = nodes.ipstart
          AND l_out.src_end = nodes.ipend
     ),0) AS "conn_out"
    ,COALESCE((SELECT SUM(links)
        FROM LinksIn AS l_in
        WHERE l_in.dst_start = nodes.ipstart
          AND l_in.dst_end = nodes.ipend
     ),0) AS "conn_in"
FROM Nodes AS nodes
WHERE EXISTS (SELECT 1 FROM LinksOut WHERE LinksOut.src_start = nodes.ipstart AND LinksOut.src_end = nodes.ipend AND LinksOut.dst_start = 3171305242 AND LinksOut.dst_end = 3171305242)

SELECT ipstart, ipend
FROM Nodes as nodes
WHERE EXISTS (SELECT 1 FROM Links WHERE Links.dst BETWEEN 3171305242 AND 3171305242 AND Links.src = nodes.ipstart);

SELECT ipstart, ipend
FROM Nodes as nodes
WHERE EXISTS (SELECT 1 FROM Links WHERE Links.dst BETWEEN 3171305216 AND 3171305471 AND Links.src = nodes.ipstart);

SELECT ipstart, ipend
FROM Nodes as nodes
WHERE EXISTS (SELECT 1 FROM Links WHERE Links.dst BETWEEN 3171287040 AND 3171352575 AND Links.src = nodes.ipstart);

SELECT ipstart, ipend
FROM Nodes as nodes
WHERE EXISTS (SELECT 1 FROM Links WHERE Links.dst BETWEEN 1325400064 AND 1342177279 AND Links.src = nodes.ipstart);
