CREATE TABLE IF NOT EXISTS datasources
(id             INT NOT NULL AUTO_INCREMENT
,name           VARCHAR(255) NOT NULL DEFAULT "New Datasource"
,ar_active      TINYINT(1) NOT NULL DEFAULT 0
,ar_interval    INT NOT NULL DEFAULT 3000
,CONSTRAINT `pk_ds` PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS settings
(datasource     INT DEFAULT NULL
,live_dest      INT DEFAULT NULL
,color_node     INT UNSIGNED NOT NULL DEFAULT 0x5555CC
,color_bg       INT UNSIGNED NOT NULL DEFAULT 0xAAFFDD
,color_tcp      INT UNSIGNED NOT NULL DEFAULT 0x5555CC
,color_udp      INT UNSIGNED NOT NULL DEFAULT 0xCC5555
,color_label    INT UNSIGNED NOT NULL DEFAULT 0x000000
,color_label_bg INT UNSIGNED NOT NULL DEFAULT 0xFFFFFF
,color_error    INT UNSIGNED NOT NULL DEFAULT 0x996666
,CONSTRAINT `fk_s` FOREIGN KEY (`datasource`) REFERENCES `datasources` (`id`)
);

-- INSERT INTO datasources (name) VALUES ("default");
-- INSERT INTO settings (datasource) VALUES (LAST_INSERT_ID());
-- INSERT INTO datasources (name) VALUES ("live");
-- INSERT INTO datasources (name) VALUES ("yesterday");
