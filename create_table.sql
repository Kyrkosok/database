CREATE TABLE `churches` (
  `wikidata` INTEGER PRIMARY KEY ,
  `label` TEXT,
  `kulturarvsdata` TEXT,
  `description` TEXT,
  `lat` REAL,
  `lon` REAL,
  `wikipedia` TEXT,
  `wp_description` TEXT,
  `commons` TEXT
)