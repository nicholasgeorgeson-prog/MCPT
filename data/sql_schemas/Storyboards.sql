CREATE TABLE "Storyboards" (
	"UUID"	INTEGER NOT NULL UNIQUE,
	"DiagramGUID"	TEXT,
	"ActivityNumber"	INTEGER,
	"Type"	TEXT,
	"StoryboardTitle"	TEXT,
	"StepNumber"	INTEGER,
	"StepType"	TEXT,
	"StoryboardOwner"	TEXT,
	PRIMARY KEY("UUID" AUTOINCREMENT),
	CONSTRAINT "DiagramGUID_CK" FOREIGN KEY("DiagramGUID","Type") REFERENCES "Diagrams"("GUID","Type") ON DELETE CASCADE
);
