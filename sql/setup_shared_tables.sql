-- Translates an IP from 1234567890 to "73.150.2.210"
DROP FUNCTION IF EXISTS decodeIP;
CREATE FUNCTION decodeIP (ip INT UNSIGNED)
RETURNS CHAR(15) DETERMINISTIC
RETURN CONCAT_WS(".", ip DIV 16777216, ip DIV 65536 MOD 256, ip DIV 256 MOD 256, ip MOD 256);

-- Listing of datasources to use
CREATE TABLE IF NOT EXISTS Datasources
(id             INT NOT NULL AUTO_INCREMENT
,name           VARCHAR(255) NOT NULL DEFAULT "New Datasource"
,ar_active      TINYINT(1) NOT NULL DEFAULT 0
,ar_interval    INT NOT NULL DEFAULT 3000
,CONSTRAINT `pk_ds` PRIMARY KEY (`id`)
);

-- User Settings
CREATE TABLE IF NOT EXISTS Settings
(datasource     INT NOT NULL
,live_dest      INT DEFAULT NULL
,color_node     INT UNSIGNED NOT NULL DEFAULT 0x5555CC
,color_bg       INT UNSIGNED NOT NULL DEFAULT 0xAAFFDD
,color_tcp      INT UNSIGNED NOT NULL DEFAULT 0x5555CC
,color_udp      INT UNSIGNED NOT NULL DEFAULT 0xCC5555
,color_label    INT UNSIGNED NOT NULL DEFAULT 0x000000
,color_label_bg INT UNSIGNED NOT NULL DEFAULT 0xFFFFFF
,color_error    INT UNSIGNED NOT NULL DEFAULT 0x996666
,CONSTRAINT `FK_sds` FOREIGN KEY (`datasource`) REFERENCES `Datasources` (`id`)
,CONSTRAINT `FK_sld` FOREIGN KEY (`live_dest`) REFERENCES `Datasources` (`id`)
);

-- Create the Nodes table
CREATE TABLE IF NOT EXISTS Nodes
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,subnet            INT NOT NULL
,alias             VARCHAR(96)
,env               VARCHAR(64)
,x                 FLOAT(12,3) DEFAULT 0
,y                 FLOAT(12,3) DEFAULT 0
,radius            FLOAT(12,3) DEFAULT 2000
,CONSTRAINT PKNodes PRIMARY KEY (ipstart, ipend)
,INDEX nenv (env)
);

-- Create the table of tags
CREATE TABLE IF NOT EXISTS Tags
(ipstart           INT UNSIGNED NOT NULL
,ipend             INT UNSIGNED NOT NULL
,tag               VARCHAR(32)
,CONSTRAINT PKTags PRIMARY KEY (ipstart, ipend, tag)
,CONSTRAINT FKTags FOREIGN KEY (ipstart, ipend) REFERENCES Nodes (ipstart, ipend)
);

-- Look-Up-Table for ports and port aliases
CREATE TABLE IF NOT EXISTS Ports
(port              INT UNSIGNED NOT NULL
,active            BOOL NOT NULL DEFAULT TRUE
,tcp               BOOL NOT NULL DEFAULT TRUE
,udp               BOOL NOT NULL DEFAULT TRUE
,name              VARCHAR(10) NOT NULL DEFAULT ""
,description       VARCHAR(255) NOT NULL DEFAULT ""
,CONSTRAINT PKPorts PRIMARY KEY (port)
);

CREATE TABLE IF NOT EXISTS PortAliases
(port              INT UNSIGNED NOT NULL
,name              VARCHAR(10) NOT NULL DEFAULT ""
,description       VARCHAR(255) NOT NULL DEFAULT ""
,CONSTRAINT PKPortAliases PRIMARY KEY (port)
);