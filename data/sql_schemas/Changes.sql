CREATE TABLE "Changes" (
	"DiagramGUID"	TEXT NOT NULL,
	"ID"	INTEGER NOT NULL,
	"Type"	TEXT DEFAULT 'Draft',
	"Date"	TIMESTAMP,
	"Version"	NUMERIC,
	"ChangeDescription"	TEXT,
	"User"	TEXT,
	PRIMARY KEY("DiagramGUID","ID","Type"),
	CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE
);
