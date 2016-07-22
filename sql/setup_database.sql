DROP TABLE IF EXISTS Links32;
DROP TABLE IF EXISTS Links24;
DROP TABLE IF EXISTS Links16;
DROP TABLE IF EXISTS Links8;
DROP TABLE IF EXISTS Nodes32;
DROP TABLE IF EXISTS Nodes24;
DROP TABLE IF EXISTS Nodes16;
DROP TABLE IF EXISTS Nodes8;
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

CREATE TABLE Links8
(source8           INT NOT NULL
,dest8             INT NOT NULL
,port              INT NOT NULL
,links             INT DEFAULT 1
,x1                FLOAT(12,3) DEFAULT 0
,y1                FLOAT(12,3) DEFAULT 0
,x2                FLOAT(12,3) DEFAULT 0
,y2                FLOAT(12,3) DEFAULT 0
,CONSTRAINT PKLinks8 PRIMARY KEY (source8, dest8, port)
);

CREATE TABLE Links16
(source8           INT NOT NULL
,source16          INT NOT NULL
,dest8             INT NOT NULL
,dest16            INT NOT NULL
,port              INT NOT NULL
,links             INT DEFAULT 1
,x1                FLOAT(12,3) DEFAULT 0
,y1                FLOAT(12,3) DEFAULT 0
,x2                FLOAT(12,3) DEFAULT 0
,y2                FLOAT(12,3) DEFAULT 0
,CONSTRAINT PKLinks16 PRIMARY KEY (source8, source16, dest8, dest16, port)
);

CREATE TABLE Links24
(source8           INT NOT NULL
,source16          INT NOT NULL
,source24          INT NOT NULL
,dest8             INT NOT NULL
,dest16            INT NOT NULL
,dest24            INT NOT NULL
,port              INT NOT NULL
,links             INT DEFAULT 1
,x1                FLOAT(12,3) DEFAULT 0
,y1                FLOAT(12,3) DEFAULT 0
,x2                FLOAT(12,3) DEFAULT 0
,y2                FLOAT(12,3) DEFAULT 0
,CONSTRAINT PKLinks24 PRIMARY KEY (source8, source16, source24, dest8, dest16, dest24, port)
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
,x1                FLOAT(12,3) DEFAULT 0
,y1                FLOAT(12,3) DEFAULT 0
,x2                FLOAT(12,3) DEFAULT 0
,y2                FLOAT(12,3) DEFAULT 0
,CONSTRAINT PKLinks32 PRIMARY KEY (source8, source16, source24, source32, dest8, dest16, dest24, dest32, port)
);
