CREATE TABLE If NOT EXISTS ds_{id}_Syslog
(entry             INT UNSIGNED NOT NULL AUTO_INCREMENT
,SourceIP          INT UNSIGNED NOT NULL
,SourcePort        INT NOT NULL
,DestinationIP     INT UNSIGNED NOT NULL
,DestinationPort   INT NOT NULL
,Timestamp         TIMESTAMP NOT NULL
,Occurances        INT DEFAULT 1 NOT NULL
,CONSTRAINT PK{id}Syslog PRIMARY KEY (entry)
);

-- -----------------------
-- Create the Temp Link tables
-- -----------------------
CREATE TABLE IF NOT EXISTS ds_{id}_staging_Links
(src               INT UNSIGNED NOT NULL
,dst               INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PK{id}tLinks PRIMARY KEY (src, dst, port, timestamp)
);

CREATE TABLE IF NOT EXISTS ds_{id}_staging_LinksIn
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PK{id}tLinksIn PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FK{id}tLinksInSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FK{id}tLinksInDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);

CREATE TABLE IF NOT EXISTS ds_{id}_staging_LinksOut
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PK{id}tLinksOut PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FK{id}tLinksOutSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FK{id}tLinksOutDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);

-- -----------------------
-- Create the Link tables
-- -----------------------
CREATE TABLE IF NOT EXISTS ds_{id}_Links
(src               INT UNSIGNED NOT NULL
,dst               INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PK{id}Links PRIMARY KEY (src, dst, port, timestamp)
);

CREATE TABLE IF NOT EXISTS ds_{id}_LinksIn
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PK{id}LinksIn PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FK{id}LinksInSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FK{id}LinksInDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);

CREATE TABLE IF NOT EXISTS ds_{id}_LinksOut
(src_start         INT UNSIGNED NOT NULL
,src_end           INT UNSIGNED NOT NULL
,dst_start         INT UNSIGNED NOT NULL
,dst_end           INT UNSIGNED NOT NULL
,port              INT NOT NULL
,timestamp         TIMESTAMP NOT NULL
,links             INT DEFAULT 1
,CONSTRAINT PK{id}LinksOut PRIMARY KEY (src_start, src_end, dst_start, dst_end, port, timestamp)
,CONSTRAINT FK{id}LinksOutSrc FOREIGN KEY (src_start, src_end) REFERENCES Nodes (ipstart, ipend)
,CONSTRAINT FK{id}LinksOutDst FOREIGN KEY (dst_start, dst_end) REFERENCES Nodes (ipstart, ipend)
);
