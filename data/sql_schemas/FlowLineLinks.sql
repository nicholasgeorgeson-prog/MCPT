CREATE TABLE "FlowLineLinks" (
	"UUID"	INTEGER UNIQUE,
	"FromGUID"	TEXT,
	"ToGUID"	TEXT,
	"LinkGUID"	TEXT,
	"Type"	TEXT,
	"LinkType"	TEXT,
	"LinkTitle"	TEXT,
	"ToMapName"	TEXT,
	"ToLevel"	TEXT,
	"Exists"	INTEGER,
	"ToLineText"	TEXT,
	"ToActivityText"	TEXT,
	"FromActivityText"	TEXT,
	"FromLineText"	TEXT,
	PRIMARY KEY("UUID" AUTOINCREMENT),
	CONSTRAINT "FromGUID" FOREIGN KEY("FromGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE,
	CONSTRAINT "ToGUID" FOREIGN KEY("ToGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE
);
