-- queries to get details about a particular IP address.
-- This file is not called directly, but used for copy/paste testing
-- Note: [201326592..218103807] refers to 12.__.__.__


SELECT conn_in8, conn_in16, temp.port, links, shortname, longname
FROM
    (SELECT (SourceIP DIV 16777216) AS 'conn_in8'
        , ((SourceIP MOD 16777216) DIV 65536) AS 'conn_in16'
        , Syslog.DestinationPort as port
        , COUNT(*) AS links
    FROM Syslog
        WHERE DestinationIP >= 201326592 && DestinationIP <= 218103807
        GROUP BY Syslog.SourceIP, Syslog.DestinationPort
    LEFT JOIN portLUT
    ON Syslog.DestinationPort = portLUT.port) AS temp
ORDER BY links DESC;
-- Inbound connections
-- WHERE clause represents the IP in question. A range means a subnet.
-- SELECT clause does division to filter only the first ip segment

SELECT (DestinationIP DIV 16777216) AS 'conn_out', COUNT(*) AS links
    FROM Syslog
    WHERE SourceIP >= 201326592 && SourceIP <= 218103807
    GROUP BY conn_out
    ORDER BY links DESC;
-- Outbound connections

SELECT temp.port, links, shortname, longname
    FROM
        (SELECT DestinationPort AS port, COUNT(*) AS links
        FROM Syslog
        WHERE DestinationIP >= 201326592 && DestinationIP <= 218103807
        GROUP BY port
        ) AS temp
        LEFT JOIN portLUT
        ON portLUT.port = temp.port
    ORDER BY links DESC
    LIMIT 50;
-- Inbound destination ports

SELECT tableA.unique_in, tableB.unique_out, tableC.unique_ports
FROM
    (SELECT COUNT(DISTINCT(SourceIP)) AS 'unique_in'
    FROM Syslog
    WHERE DestinationIP >= 201326592 && DestinationIP <= 218103807)
    AS tableA
JOIN
    (SELECT COUNT(DISTINCT(DestinationIP)) AS 'unique_out'
    FROM Syslog
    WHERE SourceIP >= 201326592 && SourceIP <= 218103807)
    AS tableB
JOIN
    (SELECT COUNT(DISTINCT(DestinationPort)) AS 'unique_ports'
    FROM Syslog
    WHERE DestinationIP >= 201326592 && DestinationIP <= 218103807)
    AS tableC;
-- Unique Inbound IP addresses
-- Unique Outbound IP addresses
-- Unique Ports