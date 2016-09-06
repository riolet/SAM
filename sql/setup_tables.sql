CREATE TABLE Nodes8
(ip8               INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,alias             VARCHAR(96)
,CONSTRAINT PKNodes8 PRIMARY KEY (ip8)
);

CREATE TABLE Nodes16
(ip8               INT NOT NULL
,ip16              INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 200
,alias             VARCHAR(96)
,CONSTRAINT PKNodes16 PRIMARY KEY (ip8, ip16)
,CONSTRAINT FKParent16 FOREIGN KEY (ip8) REFERENCES Nodes8 (ip8)
);

CREATE TABLE Nodes24
(ip8               INT NOT NULL
,ip16              INT NOT NULL
,ip24              INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 20
,alias             VARCHAR(96)
,CONSTRAINT PKNodes24 PRIMARY KEY (ip8, ip16, ip24)
,CONSTRAINT FKParent24 FOREIGN KEY (ip8, ip16) REFERENCES Nodes16 (ip8, ip16)
);

CREATE TABLE Nodes32
(ip8               INT NOT NULL
,ip16              INT NOT NULL
,ip24              INT NOT NULL
,ip32              INT NOT NULL
,connections       INT NOT NULL
,children          INT DEFAULT 0
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2
,alias             VARCHAR(96)
,CONSTRAINT PKNodes32 PRIMARY KEY (ip8, ip16, ip24, ip32)
,CONSTRAINT FKParent32 FOREIGN KEY (ip8, ip16, ip24) REFERENCES Nodes24 (ip8, ip16, ip24)
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
,timestamp         TIMESTAMP NOT NULL
,CONSTRAINT PKLinks8 PRIMARY KEY (source8, dest8, port, timestamp)
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
,timestamp         TIMESTAMP NOT NULL
,CONSTRAINT PKLinks16 PRIMARY KEY (source8, source16, dest8, dest16, port, timestamp)
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
,timestamp         TIMESTAMP NOT NULL
,CONSTRAINT PKLinks24 PRIMARY KEY (source8, source16, source24, dest8, dest16, dest24, port, timestamp)
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
,timestamp         TIMESTAMP NOT NULL
,CONSTRAINT PKLinks32 PRIMARY KEY (source8, source16, source24, source32, dest8, dest16, dest24, dest32, port, timestamp)
);
