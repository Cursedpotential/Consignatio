-- Consignatio / Intake filesystem graph
-- Target: SurrealDB 3.2.4
--
-- This migration assumes the caller has already selected the dedicated
-- Consignatio namespace and Intake database. It defines no users, credentials,
-- namespace, database, or source data.

OPTION IMPORT;

BEGIN TRANSACTION;

-- Projection control plane ---------------------------------------------------

DEFINE TABLE IF NOT EXISTS operation_run TYPE NORMAL SCHEMAFULL
  COMMENT 'One Intake projection execution. PostgreSQL/lake receipts remain canonical.';
DEFINE FIELD IF NOT EXISTS run_key ON operation_run TYPE string;
DEFINE FIELD IF NOT EXISTS tool_name ON operation_run TYPE string;
DEFINE FIELD IF NOT EXISTS tool_version ON operation_run TYPE option<string>;
DEFINE FIELD IF NOT EXISTS started_at ON operation_run TYPE datetime;
DEFINE FIELD IF NOT EXISTS completed_at ON operation_run TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS status ON operation_run TYPE string
  ASSERT $value IN ['running', 'completed', 'failed', 'superseded'];
DEFINE FIELD IF NOT EXISTS receipt_uri ON operation_run TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON operation_run TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS operation_run_key_unique ON operation_run FIELDS run_key UNIQUE;

DEFINE TABLE IF NOT EXISTS projection_snapshot TYPE NORMAL SCHEMAFULL
  COMMENT 'Immutable graph projection checkpoint derived from a canonical lake manifest.';
DEFINE FIELD IF NOT EXISTS snapshot_key ON projection_snapshot TYPE string;
DEFINE FIELD IF NOT EXISTS manifest_uri ON projection_snapshot TYPE string;
DEFINE FIELD IF NOT EXISTS manifest_sha256 ON projection_snapshot TYPE string;
DEFINE FIELD IF NOT EXISTS projected_at ON projection_snapshot TYPE datetime DEFAULT time::now();
DEFINE FIELD IF NOT EXISTS source_checkpoint ON projection_snapshot TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON projection_snapshot TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS projection_snapshot_key_unique ON projection_snapshot FIELDS snapshot_key UNIQUE;
DEFINE INDEX IF NOT EXISTS projection_snapshot_manifest_hash ON projection_snapshot FIELDS manifest_sha256;

-- Published imported facts ---------------------------------------------------
-- These tables contain observed or human-published facts only. Unpublished
-- classifier output belongs in identity_assertion or machine_proposal.

DEFINE TABLE IF NOT EXISTS store TYPE NORMAL SCHEMAFULL
  COMMENT 'A logical or physical storage boundary observed by Intake.';
DEFINE FIELD IF NOT EXISTS projection_key ON store TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON store TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON store TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS store_kind ON store TYPE string;
DEFINE FIELD IF NOT EXISTS label ON store TYPE string;
DEFINE FIELD IF NOT EXISTS root_locator ON store TYPE string;
DEFINE FIELD IF NOT EXISTS metadata ON store TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS store_projection_key_unique ON store FIELDS projection_key UNIQUE;

DEFINE TABLE IF NOT EXISTS occurrence TYPE NORMAL SCHEMAFULL
  COMMENT 'A path-level file or directory occurrence; duplicates remain separate occurrences.';
DEFINE FIELD IF NOT EXISTS projection_key ON occurrence TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON occurrence TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON occurrence TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS entry_kind ON occurrence TYPE string
  ASSERT $value IN ['file', 'directory', 'archive', 'other'];
DEFINE FIELD IF NOT EXISTS path_raw ON occurrence TYPE string;
DEFINE FIELD IF NOT EXISTS path_normalized ON occurrence TYPE string;
DEFINE FIELD IF NOT EXISTS basename ON occurrence TYPE string;
DEFINE FIELD IF NOT EXISTS size_bytes ON occurrence TYPE option<int>
  ASSERT $value = NONE OR $value >= 0;
DEFINE FIELD IF NOT EXISTS modified_at ON occurrence TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS observed_at ON occurrence TYPE datetime;
DEFINE FIELD IF NOT EXISTS metadata ON occurrence TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS occurrence_projection_key_unique ON occurrence FIELDS projection_key UNIQUE;
DEFINE INDEX IF NOT EXISTS occurrence_normalized_path ON occurrence FIELDS path_normalized;
DEFINE INDEX IF NOT EXISTS occurrence_basename ON occurrence FIELDS basename;

DEFINE TABLE IF NOT EXISTS content TYPE NORMAL SCHEMAFULL
  COMMENT 'Content identity independent of path; SHA-256 is the exact-byte identity.';
DEFINE FIELD IF NOT EXISTS projection_key ON content TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON content TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON content TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS sha256 ON content TYPE string;
DEFINE FIELD IF NOT EXISTS size_bytes ON content TYPE int ASSERT $value >= 0;
DEFINE FIELD IF NOT EXISTS media_type ON content TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON content TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS content_projection_key_unique ON content FIELDS projection_key UNIQUE;
DEFINE INDEX IF NOT EXISTS content_sha256_unique ON content FIELDS sha256 UNIQUE;

DEFINE TABLE IF NOT EXISTS representation TYPE NORMAL SCHEMAFULL
  COMMENT 'A parse, rendering, sidecar, or alternate format of content without collapsing provenance.';
DEFINE FIELD IF NOT EXISTS projection_key ON representation TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON representation TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON representation TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS representation_kind ON representation TYPE string;
DEFINE FIELD IF NOT EXISTS format ON representation TYPE option<string>;
DEFINE FIELD IF NOT EXISTS locator ON representation TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON representation TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS representation_projection_key_unique ON representation FIELDS projection_key UNIQUE;

DEFINE TABLE IF NOT EXISTS atomic_unit TYPE NORMAL SCHEMAFULL
  COMMENT 'A published organizational container preserved without flattening nested units.';
DEFINE FIELD IF NOT EXISTS projection_key ON atomic_unit TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON atomic_unit TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON atomic_unit TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS unit_kind ON atomic_unit TYPE string;
DEFINE FIELD IF NOT EXISTS label ON atomic_unit TYPE option<string>;
DEFINE FIELD IF NOT EXISTS root_occurrence ON atomic_unit TYPE option<record<occurrence>>;
DEFINE FIELD IF NOT EXISTS published_basis ON atomic_unit TYPE string;
DEFINE FIELD IF NOT EXISTS metadata ON atomic_unit TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS atomic_unit_projection_key_unique ON atomic_unit FIELDS projection_key UNIQUE;

DEFINE TABLE IF NOT EXISTS subject_account TYPE NORMAL SCHEMAFULL
  COMMENT 'An account identity explicitly published from source facts; inferred identity stays an assertion.';
DEFINE FIELD IF NOT EXISTS projection_key ON subject_account TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON subject_account TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON subject_account TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS provider ON subject_account TYPE string;
DEFINE FIELD IF NOT EXISTS account_label ON subject_account TYPE option<string>;
DEFINE FIELD IF NOT EXISTS stable_source_id ON subject_account TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON subject_account TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS subject_account_projection_key_unique ON subject_account FIELDS projection_key UNIQUE;
DEFINE INDEX IF NOT EXISTS subject_account_provider_id ON subject_account FIELDS provider, stable_source_id;

DEFINE TABLE IF NOT EXISTS export_event TYPE NORMAL SCHEMAFULL
  COMMENT 'A distinct source export event; repeated exports are never silently merged.';
DEFINE FIELD IF NOT EXISTS projection_key ON export_event TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON export_event TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON export_event TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS provider ON export_event TYPE string;
DEFINE FIELD IF NOT EXISTS requested_at ON export_event TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS generated_at ON export_event TYPE option<datetime>;
DEFINE FIELD IF NOT EXISTS source_label ON export_event TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON export_event TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS export_event_projection_key_unique ON export_event FIELDS projection_key UNIQUE;

DEFINE TABLE IF NOT EXISTS archive_series TYPE NORMAL SCHEMAFULL
  COMMENT 'A multipart archive set whose membership and ordering are preserved.';
DEFINE FIELD IF NOT EXISTS projection_key ON archive_series TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON archive_series TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON archive_series TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS series_label ON archive_series TYPE option<string>;
DEFINE FIELD IF NOT EXISTS expected_part_count ON archive_series TYPE option<int>
  ASSERT $value = NONE OR $value > 0;
DEFINE FIELD IF NOT EXISTS completeness ON archive_series TYPE string
  ASSERT $value IN ['unknown', 'incomplete', 'complete'];
DEFINE FIELD IF NOT EXISTS metadata ON archive_series TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS archive_series_projection_key_unique ON archive_series FIELDS projection_key UNIQUE;

DEFINE TABLE IF NOT EXISTS archive_part TYPE NORMAL SCHEMAFULL
  COMMENT 'One observed original archive file or multipart segment.';
DEFINE FIELD IF NOT EXISTS projection_key ON archive_part TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON archive_part TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS fact_layer ON archive_part TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS occurrence ON archive_part TYPE record<occurrence>;
DEFINE FIELD IF NOT EXISTS part_number ON archive_part TYPE option<int>
  ASSERT $value = NONE OR $value > 0;
DEFINE FIELD IF NOT EXISTS original_filename ON archive_part TYPE string;
DEFINE FIELD IF NOT EXISTS metadata ON archive_part TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS archive_part_projection_key_unique ON archive_part FIELDS projection_key UNIQUE;

-- Machine proposals ----------------------------------------------------------

DEFINE TABLE IF NOT EXISTS machine_proposal TYPE NORMAL SCHEMAFULL
  COMMENT 'Unaccepted machine output. It never overwrites imported facts or human review.';
DEFINE FIELD IF NOT EXISTS proposal_key ON machine_proposal TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON machine_proposal TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS proposed_by ON machine_proposal TYPE record<operation_run>;
DEFINE FIELD IF NOT EXISTS authority_layer ON machine_proposal TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE FIELD IF NOT EXISTS proposal_type ON machine_proposal TYPE string;
DEFINE FIELD IF NOT EXISTS confidence ON machine_proposal TYPE option<number>
  ASSERT $value = NONE OR $value IN 0..=1;
DEFINE FIELD IF NOT EXISTS rationale ON machine_proposal TYPE option<string>;
DEFINE FIELD IF NOT EXISTS features ON machine_proposal TYPE object FLEXIBLE DEFAULT {};
DEFINE FIELD IF NOT EXISTS created_at ON machine_proposal TYPE datetime DEFAULT time::now();
DEFINE INDEX IF NOT EXISTS machine_proposal_key_unique ON machine_proposal FIELDS proposal_key UNIQUE;
DEFINE INDEX IF NOT EXISTS machine_proposal_type ON machine_proposal FIELDS proposal_type;

DEFINE TABLE IF NOT EXISTS identity_assertion TYPE NORMAL SCHEMAFULL
  COMMENT 'Machine-proposed subject/account association pending an explicit human decision.';
DEFINE FIELD IF NOT EXISTS assertion_key ON identity_assertion TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON identity_assertion TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS proposed_by ON identity_assertion TYPE record<operation_run>;
DEFINE FIELD IF NOT EXISTS authority_layer ON identity_assertion TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE FIELD IF NOT EXISTS claimed_account ON identity_assertion TYPE record<subject_account>;
DEFINE FIELD IF NOT EXISTS confidence ON identity_assertion TYPE option<number>
  ASSERT $value = NONE OR $value IN 0..=1;
DEFINE FIELD IF NOT EXISTS rationale ON identity_assertion TYPE option<string>;
DEFINE FIELD IF NOT EXISTS signals ON identity_assertion TYPE object FLEXIBLE DEFAULT {};
DEFINE FIELD IF NOT EXISTS created_at ON identity_assertion TYPE datetime DEFAULT time::now();
DEFINE INDEX IF NOT EXISTS identity_assertion_key_unique ON identity_assertion FIELDS assertion_key UNIQUE;

-- Human decision overlays ----------------------------------------------------

DEFINE TABLE IF NOT EXISTS review_decision TYPE NORMAL SCHEMAFULL
  COMMENT 'Append-only human adjudication overlay; source facts and proposals are retained.';
DEFINE FIELD IF NOT EXISTS decision_key ON review_decision TYPE string;
DEFINE FIELD IF NOT EXISTS snapshot ON review_decision TYPE record<projection_snapshot>;
DEFINE FIELD IF NOT EXISTS authority_layer ON review_decision TYPE string DEFAULT 'human_decision'
  ASSERT $value = 'human_decision';
DEFINE FIELD IF NOT EXISTS reviewer_id ON review_decision TYPE string;
DEFINE FIELD IF NOT EXISTS decision ON review_decision TYPE string
  ASSERT $value IN ['accepted', 'rejected', 'needs_review', 'superseded'];
DEFINE FIELD IF NOT EXISTS reason ON review_decision TYPE option<string>;
DEFINE FIELD IF NOT EXISTS decided_at ON review_decision TYPE datetime;
DEFINE FIELD IF NOT EXISTS receipt_uri ON review_decision TYPE option<string>;
DEFINE FIELD IF NOT EXISTS metadata ON review_decision TYPE object FLEXIBLE DEFAULT {};
DEFINE INDEX IF NOT EXISTS review_decision_key_unique ON review_decision FIELDS decision_key UNIQUE;

-- Imported-fact relations ----------------------------------------------------

DEFINE TABLE IF NOT EXISTS produced_by TYPE RELATION IN projection_snapshot OUT operation_run ENFORCED SCHEMAFULL
  COMMENT 'Projection snapshot was produced by an operation run.';
DEFINE FIELD IF NOT EXISTS fact_layer ON produced_by TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE INDEX IF NOT EXISTS produced_by_unique ON produced_by FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS stored_at TYPE RELATION IN occurrence OUT store ENFORCED SCHEMAFULL
  COMMENT 'Occurrence was observed in a store.';
DEFINE FIELD IF NOT EXISTS fact_layer ON stored_at TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE INDEX IF NOT EXISTS stored_at_unique ON stored_at FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS represents TYPE RELATION IN representation OUT content ENFORCED SCHEMAFULL
  COMMENT 'Representation resolves to exact content identity.';
DEFINE FIELD IF NOT EXISTS fact_layer ON represents TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE INDEX IF NOT EXISTS represents_unique ON represents FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS occurrence_has_content TYPE RELATION IN occurrence OUT content ENFORCED SCHEMAFULL
  COMMENT 'Occurrence has exact-byte content; identical content does not collapse occurrences.';
DEFINE FIELD IF NOT EXISTS fact_layer ON occurrence_has_content TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE INDEX IF NOT EXISTS occurrence_has_content_unique ON occurrence_has_content FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS member_of TYPE RELATION IN occurrence|representation|archive_part OUT atomic_unit ENFORCED SCHEMAFULL
  COMMENT 'Published direct membership; nesting is represented separately by contains.';
DEFINE FIELD IF NOT EXISTS fact_layer ON member_of TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS ordinal ON member_of TYPE option<int> ASSERT $value = NONE OR $value >= 0;
DEFINE INDEX IF NOT EXISTS member_of_unique ON member_of FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS contains TYPE RELATION IN atomic_unit|archive_series|export_event OUT atomic_unit|archive_part|occurrence|representation ENFORCED SCHEMAFULL
  COMMENT 'Direct containment only; nested roots are preserved and never flattened.';
DEFINE FIELD IF NOT EXISTS fact_layer ON contains TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS ordinal ON contains TYPE option<int> ASSERT $value = NONE OR $value >= 0;
DEFINE INDEX IF NOT EXISTS contains_unique ON contains FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS originated_from TYPE RELATION IN occurrence|representation|atomic_unit OUT export_event|archive_part ENFORCED SCHEMAFULL
  COMMENT 'Observed origin/provenance link, not a machine inference.';
DEFINE FIELD IF NOT EXISTS fact_layer ON originated_from TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS basis ON originated_from TYPE option<string>;
DEFINE INDEX IF NOT EXISTS originated_from_unique ON originated_from FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS part_of_series TYPE RELATION IN archive_part OUT archive_series ENFORCED SCHEMAFULL
  COMMENT 'Archive segment belongs to a multipart series.';
DEFINE FIELD IF NOT EXISTS fact_layer ON part_of_series TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE INDEX IF NOT EXISTS part_of_series_unique ON part_of_series FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS belongs_to_account TYPE RELATION IN export_event|archive_series|atomic_unit OUT subject_account ENFORCED SCHEMAFULL
  COMMENT 'Published source-supported account association.';
DEFINE FIELD IF NOT EXISTS fact_layer ON belongs_to_account TYPE string DEFAULT 'imported'
  ASSERT $value = 'imported';
DEFINE FIELD IF NOT EXISTS basis ON belongs_to_account TYPE option<string>;
DEFINE INDEX IF NOT EXISTS belongs_to_account_unique ON belongs_to_account FIELDS in, out UNIQUE;

-- Machine-proposal relations -------------------------------------------------

DEFINE TABLE IF NOT EXISTS proposes_subject_for TYPE RELATION IN identity_assertion OUT export_event|archive_series|atomic_unit|occurrence ENFORCED SCHEMAFULL
  COMMENT 'Identity assertion targets a source object; it is not an accepted identity fact.';
DEFINE FIELD IF NOT EXISTS authority_layer ON proposes_subject_for TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE INDEX IF NOT EXISTS proposes_subject_for_unique ON proposes_subject_for FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS proposal_subject TYPE RELATION IN machine_proposal OUT occurrence|content|representation|atomic_unit|export_event|archive_part ENFORCED SCHEMAFULL
  COMMENT 'Machine proposal subject endpoint.';
DEFINE FIELD IF NOT EXISTS authority_layer ON proposal_subject TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE INDEX IF NOT EXISTS proposal_subject_unique ON proposal_subject FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS proposal_object TYPE RELATION IN machine_proposal OUT occurrence|content|representation|atomic_unit|export_event|archive_part ENFORCED SCHEMAFULL
  COMMENT 'Machine proposal object endpoint.';
DEFINE FIELD IF NOT EXISTS authority_layer ON proposal_object TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE INDEX IF NOT EXISTS proposal_object_unique ON proposal_object FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS possible_extraction_of TYPE RELATION IN atomic_unit|occurrence OUT archive_part|atomic_unit ENFORCED SCHEMAFULL
  COMMENT 'Machine-proposed extraction lineage; human acceptance is a separate review overlay.';
DEFINE FIELD IF NOT EXISTS proposal ON possible_extraction_of TYPE record<machine_proposal>;
DEFINE FIELD IF NOT EXISTS authority_layer ON possible_extraction_of TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE FIELD IF NOT EXISTS confidence ON possible_extraction_of TYPE option<number>
  ASSERT $value = NONE OR $value IN 0..=1;
DEFINE INDEX IF NOT EXISTS possible_extraction_proposal_unique ON possible_extraction_of FIELDS proposal UNIQUE;

DEFINE TABLE IF NOT EXISTS corroborates TYPE RELATION IN content|atomic_unit|export_event OUT content|atomic_unit|export_event ENFORCED SCHEMAFULL
  COMMENT 'Machine-proposed corroboration pending review.';
DEFINE FIELD IF NOT EXISTS proposal ON corroborates TYPE record<machine_proposal>;
DEFINE FIELD IF NOT EXISTS authority_layer ON corroborates TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE FIELD IF NOT EXISTS confidence ON corroborates TYPE option<number>
  ASSERT $value = NONE OR $value IN 0..=1;
DEFINE INDEX IF NOT EXISTS corroborates_proposal_unique ON corroborates FIELDS proposal UNIQUE;

DEFINE TABLE IF NOT EXISTS alternate_representation_of TYPE RELATION IN representation OUT representation ENFORCED SCHEMAFULL
  COMMENT 'Machine-proposed alternate-representation relationship; exact content uses represents.';
DEFINE FIELD IF NOT EXISTS proposal ON alternate_representation_of TYPE record<machine_proposal>;
DEFINE FIELD IF NOT EXISTS authority_layer ON alternate_representation_of TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE FIELD IF NOT EXISTS confidence ON alternate_representation_of TYPE option<number>
  ASSERT $value = NONE OR $value IN 0..=1;
DEFINE INDEX IF NOT EXISTS alternate_representation_proposal_unique ON alternate_representation_of FIELDS proposal UNIQUE;

DEFINE TABLE IF NOT EXISTS proposed_duplicate_of TYPE RELATION IN occurrence|atomic_unit OUT occurrence|atomic_unit ENFORCED SCHEMAFULL
  COMMENT 'Machine-proposed duplicate grouping; no occurrence or atomic unit is deleted or collapsed.';
DEFINE FIELD IF NOT EXISTS proposal ON proposed_duplicate_of TYPE record<machine_proposal>;
DEFINE FIELD IF NOT EXISTS authority_layer ON proposed_duplicate_of TYPE string DEFAULT 'machine_proposal'
  ASSERT $value = 'machine_proposal';
DEFINE FIELD IF NOT EXISTS confidence ON proposed_duplicate_of TYPE option<number>
  ASSERT $value = NONE OR $value IN 0..=1;
DEFINE INDEX IF NOT EXISTS proposed_duplicate_proposal_unique ON proposed_duplicate_of FIELDS proposal UNIQUE;

-- Human review relations -----------------------------------------------------

DEFINE TABLE IF NOT EXISTS decides_on TYPE RELATION IN review_decision OUT machine_proposal|identity_assertion ENFORCED SCHEMAFULL
  COMMENT 'Human decision adjudicates a proposal without mutating or deleting it.';
DEFINE FIELD IF NOT EXISTS authority_layer ON decides_on TYPE string DEFAULT 'human_decision'
  ASSERT $value = 'human_decision';
DEFINE INDEX IF NOT EXISTS decides_on_unique ON decides_on FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS confirms_extraction TYPE RELATION IN review_decision OUT possible_extraction_of ENFORCED SCHEMAFULL
  COMMENT 'Human acceptance overlay for a proposed extraction edge.';
DEFINE FIELD IF NOT EXISTS authority_layer ON confirms_extraction TYPE string DEFAULT 'human_decision'
  ASSERT $value = 'human_decision';
DEFINE INDEX IF NOT EXISTS confirms_extraction_unique ON confirms_extraction FIELDS in, out UNIQUE;

DEFINE TABLE IF NOT EXISTS supersedes_decision TYPE RELATION IN review_decision OUT review_decision ENFORCED SCHEMAFULL
  COMMENT 'Append-only correction chain between human decisions.';
DEFINE FIELD IF NOT EXISTS authority_layer ON supersedes_decision TYPE string DEFAULT 'human_decision'
  ASSERT $value = 'human_decision';
DEFINE INDEX IF NOT EXISTS supersedes_decision_unique ON supersedes_decision FIELDS in, out UNIQUE;

COMMIT TRANSACTION;
