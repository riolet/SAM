DROP TABLE IF EXISTS {id}_blah;

-- this is a comment and should be ignored

CREATE TABLE IF NOT EXISTS {id}_blah
(port              INT UNSIGNED NOT NULL
,CONSTRAINT PKportAliasLUT PRIMARY KEY (port)
);

SELECT * FROM {id}_blah
;

--another comment?

-- a few blank lines
