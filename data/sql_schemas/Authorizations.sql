CREATE TABLE "Authorizations" (
	"DiagramGUID"	TEXT NOT NULL,
	"Type"	TEXT NOT NULL DEFAULT 'Draft',
	"User"	TEXT NOT NULL,
	"Authorization"	TEXT,
	"SignOffStatus"	TEXT,
	"SignOffDate"	TIMESTAMP,
	"Sequence"	INTEGER,
	"RequestFrom"	TEXT,
	"DueDate"	TIMESTAMP,
	"Date"	TIMESTAMP,
	"ActiveState"	TEXT,
	PRIMARY KEY("DiagramGUID","User","Type"),
	CONSTRAINT "DiagramGUID" FOREIGN KEY("DiagramGUID") REFERENCES "Diagrams"("GUID") ON DELETE CASCADE
);
