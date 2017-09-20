DROP TABLE IF EXISTS t{id}_blah;

-- this is a comment and should be ignored

CREATE TABLE IF NOT EXISTS t{id}_blah
(port              INT UNSIGNED NOT NULL
,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)
);

SELECT * FROM t{id}_blah
;

--another comment?

-- a few blank lines

