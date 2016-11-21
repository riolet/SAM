DROP TABLE IF EXISTS Syslog;

CREATE TABLE Syslog
(entry             INT UNSIGNED NOT NULL AUTO_INCREMENT
,src               INT UNSIGNED NOT NULL
,srcport           INT NOT NULL
,dst               INT UNSIGNED NOT NULL
,dstport           INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,protocol          CHAR(8) NOT NULL
,bytes_sent        INT NOT NULL
,bytes_received    INT
,packets_sent      INT NOT NULL
,packets_received  INT
,duration          INT NOT NULL
,CONSTRAINT PKSyslog PRIMARY KEY (entry)
);