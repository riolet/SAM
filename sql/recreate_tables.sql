-- SHOW TABLES;
-- DESCRIBE Syslog;

DROP TABLE IF EXISTS Links;
DROP TABLE IF EXISTS Nodes;
DROP TABLE IF EXISTS Syslog;

CREATE TABLE Syslog
(entry             INT NOT NULL AUTO_INCREMENT
,SourceIP          INT NOT NULL
,SourcePort        INT NOT NULL
,DestinationIP     INT NOT NULL
,DestinationPort   INT NOT NULL
,Occurances        INT DEFAULT 1 NOT NULL
,CONSTRAINT PKSyslog PRIMARY KEY (entry)
);

CREATE TABLE Nodes
(IPAddress  INT NOT NULL
,CONSTRAINT PKNodes PRIMARY KEY (IPAddress)
);

CREATE TABLE Links
(SourceIP          INT NOT NULL
,DestinationIP     INT NOT NULL
,DestinationPort   INT NOT NULL
,CONSTRAINT PKLinks PRIMARY KEY (SourceIP, DestinationIP, DestinationPort)
,CONSTRAINT FKSrc FOREIGN KEY (SourceIP) REFERENCES Nodes (IPAddress)
,CONSTRAINT FKDest FOREIGN KEY (DestinationIP) REFERENCES Nodes (IPAddress)
);
