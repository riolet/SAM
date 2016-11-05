-- TESTING
SELECT *
FROM (
    SELECT COUNT(DISTINCT src)
    FROM Links
    WHERE dst BETWEEN 3502271638 AND 3502271638
    FULL OUTER JOIN
    SELECT COUNT(DISTINCT dst)
    FROM Links
    WHERE src BETWEEN 3502271638 AND 3502271638
    FULL OUTER JOIN
    SELECT COUNT(DISTINCT port)
    FROM Links
    WHERE dst BETWEEN 3502271638 AND 3502271638

-- 208.192.108.150
-- 3502271638

SELECT CONCAT(decodeIP(ipstart), CONCAT("/", subnet)) AS "address"
    , COUNT(DISTINCT l_in.src) AS "unique_in"
    , COALESCE(SUM(l_in.links),0) AS "total_in"
    , COUNT(DISTINCT l_out.dst) AS "unique_out"
    , COALESCE(SUM(l_out.links),0) AS "total_out"
FROM Nodes
LEFT JOIN Links AS l_in
    ON l_in.dst BETWEEN Nodes.ipstart AND Nodes.ipend
LEFT JOIN Links AS l_out
    ON l_out.src BETWEEN Nodes.ipstart AND Nodes.ipend
WHERE ipstart = 3186647296 AND ipend = 3186647551;


SELECT CONCAT(decodeIP(ipstart), CONCAT("/", subnet)) AS "address"
    , COUNT(DISTINCT src) AS "unique_in"
FROM Nodes
LEFT JOIN Links AS l_in
    ON l_in.dst BETWEEN Nodes.ipstart AND Nodes.ipend
WHERE ipstart = 3186647296 AND ipend = 3186647551;



(3170893824, 3187671039

SELECT CONCAT(decodeIP(ipstart), CONCAT("/", subnet)) AS "address"
    , COUNT(l_in.u_in) AS "unique_in"
    , SUM(l_in.t_in) AS "total_in"
    , COUNT(l_out.u_out) AS "unique_out"
    , SUM(l_out.t_out) AS "total_out"
FROM (
    SELECT ipstart, ipend, subnet
    FROM Nodes
    WHERE ipstart = 3170893824 AND ipend = 3187671039
) AS n
LEFT JOIN (
    SELECT 3170893824 AS 'dst', src AS 'u_in', sum(links) AS 't_in'
    FROM Links
    WHERE dst BETWEEN 3170893824 AND 3187671039
    GROUP BY src
) AS l_in
    ON l_in.dst = n.ipstart
LEFT JOIN (
    SELECT 3170893824 AS 'src', dst AS 'u_out', sum(links) AS 't_out'
    FROM Links
    WHERE src BETWEEN 3170893824 AND 3187671039
    GROUP BY dst
) AS l_out
    ON l_out.src = n.ipstart;



-- Node info
SELECT CONCAT(decodeIP(ipstart), CONCAT("/", subnet)) AS "address", alias AS "hostname"
FROM Nodes
WHERE ipstart = 3170893824 AND ipend = 3187671039;
-- Out Connections
SELECT 3170893824 AS 's1', COUNT(DISTINCT dst) AS 'unique_out', SUM(links) AS 'total_out'
FROM Links
WHERE src BETWEEN 3170893824 AND 3187671039
GROUP BY 's1';
-- In Connections, ports
SELECT 3170893824 AS 's1', COUNT(DISTINCT src) AS 'unique_in', SUM(links) AS 'total_in', COUNT(DISTINCT port) AS 'ports_used'
FROM Links
WHERE dst BETWEEN 3170893824 AND 3187671039
GROUP BY 's1';

-- COMBINED
SELECT CONCAT(decodeIP(n.ipstart), CONCAT("/", n.subnet)) AS "address"
    , n.hostname
    , l_out.unique_out
    , l_out.total_out
    , (l_out.total_out / t.seconds) AS "out / s"
    , l_in.unique_in
    , l_in.total_in
    , (l_in.total_in / t.seconds) AS "in / s"
    , l_in.ports_used
    , t.seconds
FROM (
    SELECT ipstart, subnet, alias AS "hostname"
    FROM Nodes
    WHERE ipstart = 3170893824 AND ipend = 3187671039
) AS n
LEFT JOIN (
    SELECT 3170893824 AS 's1', COUNT(DISTINCT dst) AS 'unique_out', SUM(links) AS 'total_out'
    FROM Links
    WHERE src BETWEEN 3170893824 AND 3187671039
    GROUP BY 's1'
) AS l_out
    ON n.ipstart = l_out.s1
LEFT JOIN (
    SELECT 3170893824 AS 's1', COUNT(DISTINCT src) AS 'unique_in', SUM(links) AS 'total_in', COUNT(DISTINCT port) AS 'ports_used'
    FROM Links
    WHERE dst BETWEEN 3170893824 AND 3187671039
    GROUP BY 's1'
) AS l_in
    ON n.ipstart = l_in.s1
LEFT JOIN (
    SELECT 3170893824 AS 's1'
        , (MAX(TIME_TO_SEC(timestamp)) - MIN(TIME_TO_SEC(timestamp))) AS 'seconds'
    FROM Links
    GROUP BY 's1'
) AS t
    ON n.ipstart = t.s1;
