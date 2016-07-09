SELECT COUNT(*)
    FROM Syslog
    ;
-- Result: 139118 rows in table

SELECT DestinationIP AS 'Address', COUNT(*) AS 'Connections'
    FROM Syslog
    GROUP BY Address
    ;
-- Result: 562 unique destination addresses

SELECT DestinationPort AS 'Port', COUNT(*) AS 'Connections'
    FROM Syslog
    WHERE DestinationPort < 32768
    GROUP BY Port
    ;
-- Result: 128 unique destination ports.
-- Result: 100 unique destination ports under 32768
-- Result: 31909 unique source ports

SELECT DestinationIP AS 'Address', COUNT(DISTINCT DestinationPort) AS 'Ports', COUNT(*) AS 'Connections'
    FROM Syslog
    GROUP BY Address
    ORDER BY Ports DESC, Connections DESC
    LIMIT 50
    ;
-- Result: Max 21 ports for an IP address
--         Top 40 addresses had more than 10 ports
--         By the 50th, we were down to 3 ports per address

SELECT SourceIP, DestinationIP, DestinationPort, COUNT(*) AS 'Occurrences'
    FROM Syslog
    GROUP BY SourceIP, DestinationIP, DestinationPort
    HAVING Occurrences > 100
    ORDER BY Occurrences ASC
    ;


SELECT COUNT(*)
    FROM (SELECT COUNT(*)
        FROM Syslog
        GROUP BY SourceIP, DestinationIP, DestinationPort
        HAVING COUNT(*) > 100
    ) AS cnxs;
-- Result: 11603 unique connections from a source to a destination IP and port
--         138 unique connections that occured more than 100 times
SELECT SourceIP, DestinationIP, DestinationPort, COUNT(*) AS 'Occurrences'
    FROM Syslog
    GROUP BY SourceIP, DestinationIP, DestinationPort
    HAVING Occurrences > 100
    ORDER BY Occurrences ASC
    ;
-- Verbose version of the above.  Counts connections.

SELECT DestinationIP, COUNT(*) AS cnt
    FROM Syslog
    GROUP BY DestinationIP
    HAVING (cnt > 1000)
    ;
-- Result: unique destination IP addresses, based on number of connections to them
-- HAVING cnt > 1000  =>    15 rows
-- HAVING cnt > 100   =>    99 rows
-- HAVING cnt > 10    =>   347 rows
-- HAVING cnt > 0     =>   562 rows

SELECT DestinationIP, DestinationPort, COUNT(*) AS cnt
    FROM Syslog
    GROUP BY DestinationIP, DestinationPort
    HAVING cnt > 1000
    ;
-- Result: unique destination IP:Port combos, based on number of connections to them
-- HAVING cnt > 1000  =>    13 rows
-- HAVING cnt > 100   =>   123 rows
-- HAVING cnt > 10    =>   519 rows
-- HAVING cnt > 0     =>  1571 rows

SELECT SourceIP DIV 16777215 AS 'Source', DestinationIP DIV 16777215 AS 'Destination', DestinationPort, COUNT(*) AS 'Occurrences'
    FROM Syslog
    GROUP BY Source, Destination, DestinationPort
    ORDER BY Occurrences ASC
    ;
-- 230 unique connections, 7 sources, 4 destination
