CREATE TABLE "SIPOCs" (
	"DiagramGUID"	TEXT NOT NULL,
	"Type"	TEXT NOT NULL,
	"ObjectID"	INTEGER NOT NULL,
	"ActivityID"	INTEGER,
	"Inputs"	TEXT,
	"ActivityText"	TEXT,
	"Outputs"	TEXT,
	"Resources"	TEXT,
	"ActivityCommentary"	TEXT,
	"Attatchments"	TEXT,
	"ActivityStatements"	TEXT,
	"TaskType"	TEXT,
	"Suppliers"	TEXT,
	"Customers"	TEXT,
	PRIMARY KEY("DiagramGUID","Type","ObjectID"),
	CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type") ON DELETE CASCADE
);
