DROP TABLE IF EXISTS blah;

-- this is a comment and should be ignored

CREATE TABLE IF NOT EXISTS blah
(port              INT UNSIGNED NOT NULL
,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)
);

SELECT * FROM blah
;

--another comment?

-- a few blank lines
