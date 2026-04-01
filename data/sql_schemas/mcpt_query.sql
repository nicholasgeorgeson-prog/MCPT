WITH FLLCounts AS (
    SELECT 
        FromGUID,
        SUM(CASE 
            WHEN LinkType != 'External' 
                AND Type = 'Draft' 
                AND ToLevel LIKE '%Archive%' 
            THEN 1 
            ELSE 0 
        END) AS DraftToArchive,
        SUM(CASE
            WHEN LinkType != 'External' 
                AND Type = 'Draft' 
                AND ToLevel NOT LIKE '%Draft Copy%' 
                AND (SELECT SUM(CASE WHEN LinkType != 'External' AND "Exists" = 0 THEN 1 ELSE 0 END) 
                    FROM FlowLineLinks AS FLL2 
                    WHERE FLL2.FromGUID = FLL.FromGUID) = 0 
            THEN 1 
            ELSE 0 
        END) AS DraftToMaster,
        SUM(CASE 
            WHEN LinkType != 'External' 
                AND Type = 'Master' 
                AND ToLevel LIKE '%Draft Copy%' 
            THEN 1 
            ELSE 0 
        END) AS MasterToDraft,
        SUM(CASE 
            WHEN LinkType != 'External' 
                AND ToMapName LIKE '%sandbox%' 
            THEN 1 
            ELSE 0 
        END) AS FromSandbox,
        SUM(CASE
            WHEN LinkType != 'External' 
                AND "Exists" = 0 
            THEN 1 
            ELSE 0 
        END) AS BrokenFLL
    FROM 
        FlowLineLinks FLL
    GROUP BY 
        FromGUID
),
DiagramLinkCounts AS (
    SELECT
        FromGUID,
        SUM(CASE WHEN "Exists" = 0 THEN 1 ELSE 0 END) AS DiagramLinkErrors
    FROM
        DiagramLinks
    GROUP BY
        FromGUID
),
DocumentLinkCounts AS (
    SELECT
        DiagramGUID,
        SUM(CASE WHEN "Exists" = 0 OR InRegistry = 0 THEN 1 ELSE 0 END) AS DocumentLinkErrors
    FROM
        DocumentLinks
    GROUP BY
        DiagramGUID
),
StoryboardImpacts AS (
    SELECT 
        DiagramGUID,
        STRING_AGG(StoryboardTitle || ' ' || StepType || ' ' || StepNumber, ', ') AS StoryboardImpact
    FROM 
        Storyboards
    GROUP BY 
        DiagramGUID
),
ChangeSummary AS (
    SELECT 
        DiagramGUID, 
        MAX(Date) AS LatestPromotedDate
    FROM 
        Changes 
    WHERE 
        ChangeDescription LIKE '%Promoted%' 
    GROUP BY 
        DiagramGUID
)
SELECT
    t.promotionDate AS "Promotion Date",
    CASE
        WHEN MasterLevel IS NOT NULL THEN MasterLevel
        WHEN DraftLevel LIKE '%Draft Copy' THEN SUBSTR(DraftLevel, 1, LENGTH(DraftLevel) - LENGTH('Draft Copy'))
        ELSE DraftLevel
    END AS "Level",
    t.diagramCategory AS "Diagram Category (Identify Primary & Verify Selection)",
    t.modelChangePackageTitle AS "Model Change Package Title",
    t.trbTitle as "PEACE Portal TRB Change Package Title OR Info Only",
    t.trbDescription AS "PEACE Portal TRB Change Package Description",
    t.natContact AS "NAT Contact",
    t.spFolderCreated AS "SP Folder Created",
    t.toolEntryCreated AS "Tool Entry Created",
    t.relatedFilesPosted AS "Related Files Posted",
    t.crPackageReady AS "CR Package Ready",
    t.docRegistryItemAttatched AS "Doc Registry Item Attatched",
    t.docRegistryURLUpdated AS "Updated Doc Registry URL",
    t.allDiagramsIncluded AS "All Diagrams Included In Tracker",
    t.peerReviewComplete AS "Peer Review Complete",
    t.notes AS "Notes",
    d.DraftDSLID AS "DSL UUID",
    d.DraftLevel AS "Diagram Level",
    '<draft_url_sql>' || d.DraftDSLID AS "Draft Diagram Hyperlink",
    '<master_url_sql>' || d.MasterDSLID AS "Master Diagram Hyperlink",
    d.Title AS "Diagram Title",
    d.Organization AS "Diagram Ownership by Function / CoP",
    d.Status AS "Draft Status",
    d.Status AS "Master Status",
    d.DraftTemplate AS "Draft Template",
    d.MasterTemplate AS "Master Template",
    d.Owner,
    d.DraftVersion AS "Version",
    d.MasterVersion AS "Master Version",
    auth.Authorization,
    auth.Authorizer,
    t.overlapDisposition AS "Overlap Disposition",
    CASE
        WHEN (
            SELECT COUNT(*)
            FROM Tracker t2
            WHERE t2.DiagramGUID = d.GUID
        ) > 1 THEN 'Yes'
        ELSE 'No'
    END AS "Multiple Occurrences",
    COALESCE(
        (SELECT COUNT(*)
        FROM Authorizations
        WHERE DiagramGUID = d.GUID
        AND (Authorization LIKE '%Authorization Pending%' OR Authorization LIKE '%Promotion Ready%')), 0) AS AuthorizationSent,
    COALESCE(
        (SELECT COUNT(*)
        FROM Authorizations
        WHERE DiagramGUID = d.GUID
        AND SignOffStatus LIKE 'Accepted'), 0) AS AuthorizationAccepted,
    COALESCE(
        (SELECT COUNT(*)
        FROM Authorizations
        WHERE DiagramGUID = d.GUID), 0) AS TotalAuthorizations,
    CASE 
        WHEN COUNT(CASE 
            WHEN User NOT LIKE '<TRB_chair>' THEN 1 
            ELSE 0 
        END) = 0 THEN 'No'
        ELSE 
            CASE 
                WHEN COUNT(CASE 
                    WHEN SignOffStatus = 'Accepted' AND User NOT LIKE '<TRB_chair>' THEN 1 
                    ELSE 0 
                END) = COUNT(CASE 
                    WHEN User NOT LIKE '<TRB_chair>' THEN 1 
                    ELSE 0 
                END) THEN 'Yes'
                ELSE 'No'
            END
    END AS "Authorized by POC",
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM Authorizations 
            WHERE DiagramGUID = d.GUID 
            AND User = '<TRB_chair>'
            AND SignOffStatus = 'Signed Off'
        ) THEN 'Yes'
        ELSE 
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM Authorizations 
                    WHERE DiagramGUID = d.GUID 
                    AND User = '<TRB_chair>'
                    AND SignOffStatus != 'Signed Off'
                ) THEN 'No'
                ELSE 'N/A'
            END
    END AS "Authorized by Eng Process TRB Chair",
    STRFTIME('%m/%d/%Y', cs.LatestPromotedDate) AS "Last Promotion Date",
    CASE 
        WHEN d.DraftTemplate LIKE '%In-work%' THEN 'No'
        ELSE 'Yes'
    END AS "Post-Promotion Template Changed in Draft (Not In-work)",
    CASE 
        WHEN d.MasterTemplate LIKE '%In-work%' THEN 'No'
        ELSE 'Yes'
    END AS "Post-Promotion Template Changed in Master (Not In-work)",
    CASE 
        WHEN d.Status = 'Engineering Approved' 
            AND NOT d.DraftTemplate LIKE '%Engineering Approved%' THEN 'Warning'
        ELSE 'Good'
    END AS "Non-engineering Approved Diagram Templates",
    COALESCE(fc.DraftToArchive, 0) AS "Links from Draft to Archive",
    COALESCE(fc.DraftToMaster, 0) AS "Links from Draft to Master",
    COALESCE(fc.MasterToDraft, 0) AS "Links from Master to Draft",
    COALESCE(fc.FromSandbox, 0) AS "Links from Sandbox",
    COALESCE(dilc.DiagramLinkErrors, 0) AS "Diagram Links Errors",
    COALESCE(dolc.DocumentLinkErrors, 0) AS "Document Links Errors",
    COALESCE(fc.BrokenFLL, 0) AS "Broken FLL",
    (
        COALESCE(fc.DraftToArchive, 0) + 
        COALESCE(fc.DraftToMaster, 0) + 
        COALESCE(fc.MasterToDraft, 0) + 
        COALESCE(fc.FromSandbox, 0) + 
        COALESCE(dilc.DiagramLinkErrors, 0) + 
        COALESCE(dolc.DocumentLinkErrors, 0) +
        COALESCE(fc.BrokenFLL, 0)
    ) AS "Total Errors",
    d.URL AS "URL",
    COALESCE(si.StoryboardImpact, '') AS "Storyboard Impact",
    COALESCE(
        (SELECT COUNT(*)
        FROM Changes
        WHERE DiagramGUID = d.GUID
        AND Date > cs.LatestPromotedDate),
        0) AS "Changes Since Last Promotion",
    COALESCE(
        (SELECT 
            STRING_AGG('• ' || ChangeDescription || ' (' || User || ' - ' || STRFTIME('%m/%d/%Y', Date) || '), ', '\n') AS ChangeLogEntries
        FROM
            Changes
        WHERE 
            DiagramGUID = d.GUID
            AND Date > cs.LatestPromotedDate
        GROUP BY
            DiagramGUID
        )
    , '') AS "Change Log Entries",
    d.MasterDSLID AS "Master DSLID",
    d.GUID AS "GUID"
FROM 
    Diagrams d
LEFT JOIN 
    ChangeSummary cs ON d.GUID = cs.DiagramGUID
LEFT JOIN 
    (SELECT 
        DiagramGUID,
        Authorization,
        CASE 
            WHEN COUNT(User) = 1 THEN MAX(User)
            WHEN COUNT(User) = 2 THEN MAX(CASE WHEN User != '<TRB_chair>' THEN User END)
            ELSE ''
        END AS Authorizer
    FROM 
        Authorizations
    GROUP BY 
        DiagramGUID) auth ON d.GUID = auth.DiagramGUID
LEFT JOIN 
    Authorizations a ON d.GUID = a.DiagramGUID
LEFT JOIN 
    FLLCounts fc ON d.GUID = fc.FromGUID
LEFT JOIN
    DiagramLinkCounts dilc ON d.GUID = dilc.FromGUID
LEFT JOIN
    DocumentLinkCounts dolc ON d.GUID = dolc.DiagramGUID
LEFT JOIN
    StoryboardImpacts si ON d.GUID = si.DiagramGUID
LEFT JOIN
    Tracker t ON d.GUID = t.DiagramGUID
WHERE 
    d.GUID IN (SELECT DiagramGUID FROM Tracker)
GROUP BY d.GUID;