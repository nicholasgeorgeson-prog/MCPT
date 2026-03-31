CREATE TABLE "DocumentLinks" (
	"UUID"	INTEGER NOT NULL UNIQUE,
	"DiagramGUID"	TEXT,
	"Type"	TEXT,
	"DocumentNo"	INTEGER,
	"InRegistry"	INTEGER,
	"ActivityID"	TEXT,
	"LinkTitle"	TEXT,
	"FileName"	TEXT,
	"FileType"	TEXT,
	"Exists"	INTEGER,
	"DocumentOwner"	TEXT,
	"ActivityResources"	TEXT,
	"ObjectText"	TEXT,
	PRIMARY KEY("UUID" AUTOINCREMENT),
	CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE
);
