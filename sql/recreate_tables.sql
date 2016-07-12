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
(IPAddress         INT NOT NULL
,connections       INT NOT NULL
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,alias             VARCHAR(96)
,CONSTRAINT PKNodes8 PRIMARY KEY (IPAddress)
);

CREATE TABLE Nodes16
(parent8           INT NOT NULL
,IPAddress         INT NOT NULL
,connections       INT NOT NULL
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 200
,alias             VARCHAR(96)
,CONSTRAINT PKNodes16 PRIMARY KEY (parent8, IPAddress)
,CONSTRAINT FKParent16 FOREIGN KEY (parent8) REFERENCES Nodes8 (IPAddress)
);

CREATE TABLE Nodes24
(parent8           INT NOT NULL
,parent16          INT NOT NULL
,IPAddress         INT NOT NULL
,connections       INT NOT NULL
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 20
,alias             VARCHAR(96)
,CONSTRAINT PKNodes24 PRIMARY KEY (parent8, parent16, IPAddress)
,CONSTRAINT FKParent24 FOREIGN KEY (parent8, parent16) REFERENCES Nodes16 (parent8, IPAddress)
);

CREATE TABLE Nodes32
(parent8           INT NOT NULL
,parent16          INT NOT NULL
,parent24          INT NOT NULL
,IPAddress         INT NOT NULL
,connections       INT NOT NULL
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2
,alias             VARCHAR(96)
,CONSTRAINT PKNodes32 PRIMARY KEY (parent8, parent16, parent24, IPAddress)
,CONSTRAINT FKParent32 FOREIGN KEY (parent8, parent16, parent24) REFERENCES Nodes24 (parent8, parent16, IPAddress)
);

CREATE TABLE Links
(SourceIP          INT UNSIGNED NOT NULL
,DestinationIP     INT UNSIGNED NOT NULL
,DestinationPort   INT NOT NULL
,CONSTRAINT PKLinks PRIMARY KEY (SourceIP, DestinationIP, DestinationPort)
,CONSTRAINT FKSrc FOREIGN KEY (SourceIP) REFERENCES Nodes (IPAddress)
,CONSTRAINT FKDest FOREIGN KEY (DestinationIP) REFERENCES Nodes (IPAddress)
);
