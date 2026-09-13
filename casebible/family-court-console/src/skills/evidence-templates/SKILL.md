---
name: fct-evidence-templates
description: "(family-court-toolkit) Evidence intake, cataloging, chain of custody, hash verification, exhibit preparation, and quality control templates for digital evidence processing in legal proceedings."
---
> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — restored as a first-class skill (was `references/evidence-templates` under the `family-court-toolkit` entry skill; owner ruling 15:23)._
# Evidence Templates

Reusable templates for digital evidence processing, chain of custody documentation, and court-ready exhibit preparation.

## Evidence Intake Log

```
EVIDENCE INTAKE LOG
===================
Date Received: [YYYY-MM-DD HH:MM]
Source: [device/account/platform]
Format: [file type, extraction method]
Hash (MD5): [calculated MD5 hash]
Hash (SHA-256): [calculated SHA-256 hash]
Description: [what it contains]
Relevance: [which issues it relates to]
Priority: [high/medium/low]
Status: [raw/processed/indexed/ready]
Received From: [person/entity]
Received By: [your name/role]
Storage Location: [file path]
Notes: [any observations, anomalies, or concerns]
```

## File Organization System

```
/Evidence
  /01_Communications
    /Text_Messages
      /[Phone_Number]_[Contact_Name]
        - raw_export.txt
        - parsed_messages.csv
        - metadata.json
        - chain_of_custody.md
    /Emails
      /[Account]
        - raw_mbox/
        - parsed_emails.csv
        - headers_analysis.txt
        - thread_reconstruction.md
    /Social_Media
      /[Platform]
        - raw_download/
        - parsed_content.csv
        - media/
        - metadata_extract.json
    /Chat_Apps
      /[App_Name]
        - export/
        - parsed/
        - media/

  /02_Documents
    /Financial
    /Legal
    /Medical
    /School
    /Employment

  /03_Media
    /Photos
      /[Source]
        - originals/
        - exif_data.csv
        - manipulation_analysis.md
    /Videos
      /[Source]
        - originals/
        - metadata.json
        - transcripts/
    /Audio
      /[Source]
        - originals/
        - metadata.json
        - transcripts/

  /04_Records
    /Phone_Records
    /Location_Data
    /Account_Statements
    /Court_Documents
    /Medical_Records

  /05_Analysis
    /Timelines
    /Summaries
    /Cross_References
    /Exhibits
      /Exhibit_[Number]

  /06_Working
    /In_Progress
    /To_Review
    /Questions
    /Duplicates
```

## Chain of Custody Log

```
CHAIN OF CUSTODY
================
Evidence ID: [unique identifier]
Description: [brief description]
Original Hash (MD5): [hash]
Original Hash (SHA-256): [hash]

CUSTODY LOG:
------------
[YYYY-MM-DD HH:MM] Received from [person/source] by [your name]
                   Condition: [describe state of evidence]
                   Storage: [where stored]

[YYYY-MM-DD HH:MM] Accessed by [name] for [purpose]
                   Action: [what was done]
                   Hash verified: [MATCH/MISMATCH]

[YYYY-MM-DD HH:MM] Processed by [name]
                   Action: [specific processing steps]
                   Output: [files created]
                   Original preserved: [YES/NO]

[YYYY-MM-DD HH:MM] Transferred to [person/agent] for [purpose]
                   Hash verified: [MATCH/MISMATCH]
                   Received by: [signature/confirmation]

CURRENT STATUS: [location/custodian]
INTEGRITY: [verified/compromised]
```

## Hash Verification Log

```
HASH VERIFICATION LOG
=====================
File: [filename]
Original Hash (MD5): [hash from intake]
Original Hash (SHA-256): [hash from intake]
Date Verified: [YYYY-MM-DD]
Current Hash (MD5): [recalculated]
Current Hash (SHA-256): [recalculated]
Status: [MATCH / MISMATCH]
Verified By: [name]
```

**Tools:**
- Windows: `certutil -hashfile [file] MD5` and `certutil -hashfile [file] SHA256`
- Linux/Mac: `md5sum [file]` and `sha256sum [file]`

## Exhibit Preparation Template

```
EXHIBIT [Letter/Number]
=======================
Case: [case name]
Description: [what this exhibit shows]
Source: [where evidence came from]
Date Range: [if applicable]
Prepared By: [your name]
Date Prepared: [YYYY-MM-DD]

AUTHENTICATION
--------------
Original File: [filename]
Hash (MD5): [hash]
Hash (SHA-256): [hash]
Received From: [source]
Date Received: [date]
Chain of Custody: [reference to custody log]

CONTENT
-------
[Formatted, redacted as needed, annotated]

[For text messages: conversation format with timestamps]
[For emails: header info + body]
[For photos: image with caption showing date/time/location]
[For documents: clean, readable format]

METADATA
--------
[Relevant metadata that authenticates or provides context]
- Timestamp: [from EXIF/headers]
- Location: [if applicable]
- Device: [if applicable]
- [Other relevant technical details]

RELEVANCE
---------
[Brief explanation of why this exhibit matters to the case]

NOTES
-----
[Any redactions, explanations, or caveats]
```

## Evidence Summary Report

```
EVIDENCE SUMMARY REPORT
=======================
Case: [case name/number]
Prepared By: [your name]
Date: [YYYY-MM-DD]
Evidence Period: [date range covered]

EVIDENCE INVENTORY
------------------
Total Items: [number]
  - Text Messages: [count] ([date range])
  - Emails: [count] ([date range])
  - Photos: [count] ([date range])
  - Videos: [count] ([date range])
  - Social Media: [count] ([platforms])
  - Documents: [count] ([types])
  - Other: [count] ([types])

KEY FINDINGS
------------
1. [Finding with evidence reference]
2. [Finding with evidence reference]
3. [Finding with evidence reference]

TIMELINE HIGHLIGHTS
-------------------
[YYYY-MM-DD] - [Event with evidence reference]
[YYYY-MM-DD] - [Event with evidence reference]
[YYYY-MM-DD] - [Event with evidence reference]

INTEGRITY STATUS
----------------
All evidence hashed: [YES/NO]
Chain of custody maintained: [YES/NO]
Issues identified: [number] (see attached issue log)

EXHIBITS PREPARED
-----------------
Exhibit A: [description]
Exhibit B: [description]
[etc.]

LIMITATIONS & NOTES
-------------------
[Any gaps, missing data, technical limitations, or caveats]
```

## Timeline Export Format

CSV format for import into timeline tools or spreadsheet:

```csv
Date,Time,Source,Type,From,To,Content,Location,Evidence_ID,Notes
```

**Fields:**
- **Date/Time**: When event occurred
- **Source**: Platform/device
- **Type**: Message type
- **From/To**: Parties involved
- **Content**: Brief description or excerpt
- **Location**: GPS or mentioned location
- **Evidence_ID**: Unique identifier linking to full evidence
- **Notes**: Relevance, flags, observations

## Processing Checklist

Before marking evidence as "ready":

- [ ] **Original file preserved** - No modifications to source file
- [ ] **Hash verified** - Current hash matches intake hash
- [ ] **Metadata extracted** - All available metadata documented
- [ ] **Chain of custody complete** - Every action logged
- [ ] **Organized properly** - Filed in correct folder structure
- [ ] **Indexed** - Searchable and cross-referenced
- [ ] **Flagged items reviewed** - Important content identified
- [ ] **Quality checked** - Readable, complete, no corruption
- [ ] **Duplicates identified** - Redundant files noted
- [ ] **Documentation complete** - Processing notes, observations, limitations

## Issue Flag Template

```
ISSUE FLAG
==========
File/Item: [identifier]
Issue Type: [Missing Metadata / Timestamp Anomaly / Gap in Data /
            Authentication Failure / Manipulation Indicator /
            Duplicate Content / Corrupted File / Inconsistent Format]
Description: [specific problem]
Impact: [how this affects evidence value]
Recommendation: [further analysis? expert needed? exclude?]
Flagged By: [name]
Date: [YYYY-MM-DD]
```

## Timestamp Analysis Template

```
TIMESTAMP ANALYSIS
==================
File: [filename]
File Created: [date]
File Modified: [date]
EXIF Original: [date]
EXIF Digitized: [date]
Software: [if present]

Discrepancy: [describe any inconsistencies]
Conclusion: [likely explanation]
Recommendation: [further analysis needed? admissible as-is?]
```

**Red Flags:**
- File modified date AFTER EXIF original date -> possible editing
- EXIF date missing or zeroed out -> metadata stripped
- File created date significantly different from EXIF -> transferred/copied
- Editing software in EXIF -> image was processed

## Location Analysis Template

```
LOCATION ANALYSIS
=================
File: [filename]
Date/Time: [from EXIF]
Coordinates: [lat, long]
Location: [address/description from map]
Relevance: [how this relates to case]
Corroboration: [supports/contradicts what claim?]
```

## Ethical Guidelines

1. **Never modify original evidence** - Always preserve originals, work on copies
2. **Document everything** - Every action logged in chain of custody
3. **Note limitations** - Missing data, technical limitations, uncertainty
4. **Preserve exculpatory evidence** - Don't cherry-pick; flag evidence that helps both sides
5. **Maintain confidentiality** - Secure storage, appropriate redaction

## Added 2026-09-07 from Drive intake (source: "Snap Subpoena, Pro Se Guide.docx")

### Pro se subpoena to a social-media platform — content vs. non-content data

Generic (jurisdiction-neutral federal framework) guide for what a pro se litigant can realistically obtain
from a social-media provider (the intake example was Snapchat/Snap Inc., but the content-vs-non-content
distinction applies to any US-based platform):

- **The Stored Communications Act (SCA)**, 18 U.S.C. § 2701 et seq. (part of ECPA, 1986), draws a hard line:
  - **Content of communications** (message text, photo/video content, voice message audio) — providers are
    barred from voluntarily disclosing this to a non-governmental party under almost any circumstance. A
    civil discovery subpoena is **not** one of the exceptions; a subpoena demanding message *content* from
    the platform directly will almost certainly be challenged and quashed.
  - **Non-content records / basic subscriber information** (metadata: who, when, from what IP/device;
    account registration info; login history) — this is the realistic target of a civil subpoena, and it can
    still be strategically valuable (e.g., corroborating or contradicting a timeline).
- **Practical guidance for intake/exhibit-list drafting:** when a client wants to subpoena a platform, set
  the expectation up front that content will very likely be unobtainable and scope the subpoena to
  non-content metadata; consider whether the same information (screenshots, exports) can instead be obtained
  directly from a party who has account access, subject to the authorization/legality checks in
  `mre-authentication`'s "unauthorized access" note above.
- Distance for the current subpoena target's exact procedure (registered agent, required cover letter,
  witness fee) from the generic pattern here — this guide gives the legal *framework*, not a specific
  platform's current process, which changes and must be verified at intake time.

> _Byline: Claude Code · Fable 5.1 · 2026-09-07 — Drive intake mining, see
> `content/custody-guide/sources/DRIVE-INTAKE-LEDGER-2026-09-07.md`._
