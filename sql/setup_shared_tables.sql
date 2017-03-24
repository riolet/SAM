-- Translates an IP from 1234567890 to "73.150.2.210"
DROP FUNCTION IF EXISTS decodeIP;
CREATE FUNCTION decodeIP (ip INT UNSIGNED)
RETURNS CHAR(15) DETERMINISTIC
RETURN CONCAT_WS(".", ip DIV 16777216, ip DIV 65536 MOD 256, ip DIV 256 MOD 256, ip MOD 256);
-- Translates an IP from (73, 150, 2, 210) to 1234567890
DROP FUNCTION IF EXISTS encodeIP;
CREATE FUNCTION encodeIP (ip8 INT, ip16 INT, ip24 INT, ip32 INT)
RETURNS INT UNSIGNED DETERMINISTIC
RETURN (ip8 * 16777216 + ip16 * 65536 + ip24 * 256 + ip32);

-- track subscriptions
CREATE TABLE IF NOT EXISTS Subscriptions
(subscription   INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY
,email          VARCHAR(254) NOT NULL UNIQUE
,name           TEXT NOT NULL
,plan           TEXT NOT NULL
,groups         TEXT NOT NULL
,active         BOOL NOT NULL DEFAULT FALSE
);

-- Listing of datasources to use
CREATE TABLE IF NOT EXISTS Datasources
(id             INT NOT NULL AUTO_INCREMENT
,subscription   INTEGER NOT NULL
,name           VARCHAR(255) NOT NULL DEFAULT "default"
,ar_active      TINYINT(1) NOT NULL DEFAULT 0
,ar_interval    INT NOT NULL DEFAULT 300
,CONSTRAINT `PK_ids` PRIMARY KEY (`id`)
,CONSTRAINT `FK_sds` FOREIGN KEY (`subscription`) REFERENCES `Subscriptions` (`subscription`)
);

-- User Settings
CREATE TABLE IF NOT EXISTS Settings
(subscription   INTEGER NOT NULL PRIMARY KEY
,datasource     INT NOT NULL
,color_node     INT UNSIGNED NOT NULL DEFAULT 0x5555CC
,color_bg       INT UNSIGNED NOT NULL DEFAULT 0xAAFFDD
,color_tcp      INT UNSIGNED NOT NULL DEFAULT 0x5555CC
,color_udp      INT UNSIGNED NOT NULL DEFAULT 0xCC5555
,color_label    INT UNSIGNED NOT NULL DEFAULT 0x000000
,color_label_bg INT UNSIGNED NOT NULL DEFAULT 0xFFFFFF
,color_error    INT UNSIGNED NOT NULL DEFAULT 0x996666
,CONSTRAINT `FK_dss` FOREIGN KEY (`datasource`) REFERENCES `Datasources` (`id`)
,CONSTRAINT `FK_ss` FOREIGN KEY (`subscription`) REFERENCES `Subscriptions` (`subscription`)
);

-- Default Look-Up-Table for ports
CREATE TABLE IF NOT EXISTS Ports
(port              INT UNSIGNED NOT NULL PRIMARY KEY
,protocols         TEXT
,name              VARCHAR(10) NOT NULL DEFAULT ""
,description       VARCHAR(255) NOT NULL DEFAULT ""
);

-- Key table for live updates
CREATE TABLE IF NOT EXISTS LiveKeys
(access_key     CHAR(24) PRIMARY KEY
,subscription   INTEGER NOT NULL
,datasource     INT NOT NULL
,created        TIMESTAMP DEFAULT NOW()
,CONSTRAINT `FK_lks` FOREIGN KEY (`subscription`) REFERENCES `Subscriptions` (`subscription`)
,CONSTRAINT `FK_lkd` FOREIGN KEY (`datasource`) REFERENCES `Datasources` (`id`)
);
