-- SHOW TABLES;
-- DESCRIBE Syslog;

DROP TABLE IF EXISTS Links;
DROP TABLE IF EXISTS Nodes;
DROP TABLE IF EXISTS Syslog;

CREATE TABLE Syslog
(entry             INT UNSIGNED NOT NULL AUTO_INCREMENT
,SourceIP          INT UNSIGNED NOT NULL
,SourcePort        INT NOT NULL
,DestinationIP     INT UNSIGNED NOT NULL
,DestinationPort   INT NOT NULL
,Occurances        INT DEFAULT 1 NOT NULL
,CONSTRAINT PKSyslog PRIMARY KEY (entry)
);

CREATE TABLE Nodes8
(address           INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,alias             VARCHAR(96)
,CONSTRAINT PKNodes8 PRIMARY KEY (address)
);

CREATE TABLE Nodes16
(parent8           INT NOT NULL
,address           INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 200
,alias             VARCHAR(96)
,CONSTRAINT PKNodes16 PRIMARY KEY (parent8, address)
,CONSTRAINT FKParent16 FOREIGN KEY (parent8) REFERENCES Nodes8 (address)
);

CREATE TABLE Nodes24
(parent8           INT NOT NULL
,parent16          INT NOT NULL
,address           INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 20
,alias             VARCHAR(96)
,CONSTRAINT PKNodes24 PRIMARY KEY (parent8, parent16, address)
,CONSTRAINT FKParent24 FOREIGN KEY (parent8, parent16) REFERENCES Nodes16 (parent8, address)
);

CREATE TABLE Nodes32
(parent8           INT NOT NULL
,parent16          INT NOT NULL
,parent24          INT NOT NULL
,address           INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2
,alias             VARCHAR(96)
,CONSTRAINT PKNodes32 PRIMARY KEY (parent8, parent16, parent24, address)
,CONSTRAINT FKParent32 FOREIGN KEY (parent8, parent16, parent24) REFERENCES Nodes24 (parent8, parent16, address)
);

--I think I only need Links32
CREATE TABLE Links8
(source8           INT NOT NULL
,dest8             INT NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinks8 PRIMARY KEY (source8, dest8)
,CONSTRAINT FKSource8 FOREIGN KEY (source8) REFERENCES Nodes8 (address)
,CONSTRAINT FKDest8 FOREIGN KEY (dest8) REFERENCES Nodes8 (address)
);
--I think I only need Links32
CREATE TABLE Links16
(source8           INT NOT NULL
,source16          INT NOT NULL
,dest8             INT NOT NULL
,dest16            INT NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinks16 PRIMARY KEY (source8, source16, dest8, dest16)
,CONSTRAINT FKSource16 FOREIGN KEY (source8, source16) REFERENCES Nodes16 (parent8, address)
,CONSTRAINT FKDest16 FOREIGN KEY (dest8, dest16) REFERENCES Nodes16 (parent8, address)
);
--I think I only need Links32
CREATE TABLE Links24
(source8           INT NOT NULL
,source16          INT NOT NULL
,source24          INT NOT NULL
,dest8             INT NOT NULL
,dest16            INT NOT NULL
,dest24            INT NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinks24 PRIMARY KEY (source8, source16, source24, dest8, dest16, dest24)
,CONSTRAINT FKSource24 FOREIGN KEY (source8, source16, source24) REFERENCES Nodes24 (parent8, parent16, address)
,CONSTRAINT FKDest24 FOREIGN KEY (dest8, dest16, dest24) REFERENCES Nodes24 (parent8, parent16, address)
);

CREATE TABLE Links32
(source8           INT NOT NULL
,source16          INT NOT NULL
,source24          INT NOT NULL
,source32          INT NOT NULL
,dest8             INT NOT NULL
,dest16            INT NOT NULL
,dest24            INT NOT NULL
,dest32            INT NOT NULL
,port              INT NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PKLinks32 PRIMARY KEY (source8, source16, source24, source32, dest8, dest16, dest24, dest32, port)
,CONSTRAINT FKSource32 FOREIGN KEY (source8, source16, source24, source32) REFERENCES Nodes32 (parent8, parent16, parent24, address)
,CONSTRAINT FKDest32 FOREIGN KEY (dest8, dest16, dest24, dest32) REFERENCES Nodes32 (parent8, parent16, parent24, address)
);


INSERT INTO Links32 (source8, source16, source24, source32, dest8, dest16, dest24, dest32, port, links)
SELECT SourceIP DIV 16777216 AS source8
     , (SourceIP - (SourceIP DIV 16777216) * 16777216) DIV 65536 AS source16
     , (SourceIP - (SourceIP DIV 65536) * 65536) DIV 256 AS source24
     , (SourceIP - (SourceIP DIV 256) * 256) AS source32
     , DestinationIP DIV 16777216 AS dest8
     , (DestinationIP - (DestinationIP DIV 16777216) * 16777216) DIV 65536 AS dest16
     , (DestinationIP - (DestinationIP DIV 65536) * 65536) DIV 256 AS dest24
     , (DestinationIP - (DestinationIP DIV 256) * 256) AS dest32
     , DestinationPort AS port
     , COUNT(*) AS conns
FROM Syslog
GROUP BY source8, source16, source24, source32, dest8, dest16, dest24, dest32, port;
