DROP TABLE IF EXISTS portLUT;

CREATE TABLE portLUT
(port              INT UNSIGNED NOT NULL
,active            BOOL NOT NULL DEFAULT TRUE
,tcp               BOOL NOT NULL DEFAULT TRUE
,udp               BOOL NOT NULL DEFAULT TRUE
,shortname         VARCHAR(10) NOT NULL DEFAULT ""
,longname          VARCHAR(255) NOT NULL DEFAULT ""
,alias_shortname   VARCHAR(10)
,alias_longname    VARCHAR(255)
,CONSTRAINT PKportLUT PRIMARY KEY (port)
);