# Iteration Index — every schema / table / parser / migration across all prior GitHub iterations

> Generated 2026-07-05 23:21 · 2080 artifacts across 12 iterations.
> Persistent catalog: `D:/casebible/iterations_index.duckdb` (tables `iteration_index`, `table_defs`).
> Query e.g.: `SELECT iteration, rel_path FROM iteration_index WHERE defines ILIKE '%sms_messages%'`.

## Artifacts per iteration

| iteration | artifacts |
|---|---|
| Agno-MCP-Platform | 595 |
| dial-stack | 595 |
| OTHER_RESOURCES_TO_SORT | 566 |
| TheBigOne | 87 |
| The_Platform_Archive | 80 |
| Agno-MCP-Platform-alpha | 34 |
| _project_dirs_loose | 34 |
| extracted-code | 27 |
| dev_docs_artifacts | 18 |
| mcp-tool-platform | 17 |
| TEMP_GITHUB_COMPARE | 17 |
| platform_pbackup | 10 |

## By kind

| kind | count |
|---|---|
| parser | 1568 |
| sql_schema | 168 |
| schema_def | 155 |
| sql_migration | 94 |
| drizzle_schema | 73 |
| ontology | 22 |

## Distinct table/entity names defined (298) — name → iterations defining it

| table/entity | # iters | iterations |
|---|---|---|
| `_PromptContributors` | 1 | OTHER_RESOURCES_TO_SORT |
| `accounts` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `actions` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `activities` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `agentConfigurations` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `agent_memories` | 3 | OTHER_RESOURCES_TO_SORT, TheBigOne, The_Platform_Archive |
| `agent_run` | 3 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, extracted-code |
| `agents` | 1 | OTHER_RESOURCES_TO_SORT |
| `ai.agno_approvals` | 1 | Agno-MCP-Platform |
| `ai.agno_component_configs` | 1 | Agno-MCP-Platform |
| `ai.agno_component_links` | 1 | Agno-MCP-Platform |
| `ai.agno_components` | 1 | Agno-MCP-Platform |
| `ai.agno_eval_runs` | 1 | Agno-MCP-Platform |
| `ai.agno_learnings` | 1 | Agno-MCP-Platform |
| `ai.agno_memories` | 1 | Agno-MCP-Platform |
| `ai.agno_metrics` | 1 | Agno-MCP-Platform |
| `ai.agno_schedule_runs` | 1 | Agno-MCP-Platform |
| `ai.agno_schedules` | 1 | Agno-MCP-Platform |
| `ai.agno_schema_versions` | 1 | Agno-MCP-Platform |
| `ai.agno_sessions` | 1 | Agno-MCP-Platform |
| `ai.api_keys` | 1 | Agno-MCP-Platform |
| `ai.casebible_evidence_contents` | 1 | Agno-MCP-Platform |
| `ai.casebible_evidence_test_contents` | 1 | Agno-MCP-Platform |
| `ai.casebible_ingest_test2_contents` | 1 | Agno-MCP-Platform |
| `ai.casebible_ingest_test_contents` | 1 | Agno-MCP-Platform |
| `ai.platform_knowledge_contents` | 1 | Agno-MCP-Platform |
| `analysis.account` | 1 | Agno-MCP-Platform |
| `analysis.artifact_registry` | 1 | Agno-MCP-Platform |
| `analysis.attachment` | 1 | Agno-MCP-Platform |
| `analysis.behavior_category` | 1 | Agno-MCP-Platform |
| `analysis.behavior_category_mcl` | 1 | Agno-MCP-Platform |
| `analysis.call_log` | 1 | Agno-MCP-Platform |
| `analysis.completion_evidence` | 1 | Agno-MCP-Platform |
| `analysis.conversation` | 1 | Agno-MCP-Platform |
| `analysis.custody_factor` | 1 | Agno-MCP-Platform |
| `analysis.detection_pattern` | 1 | Agno-MCP-Platform |
| `analysis.detection_pattern_set` | 1 | Agno-MCP-Platform |
| `analysis.device` | 1 | Agno-MCP-Platform |
| `analysis.discovery_request` | 1 | Agno-MCP-Platform |
| `analysis.discovery_request_revision` | 1 | Agno-MCP-Platform |
| `analysis.email` | 1 | Agno-MCP-Platform |
| `analysis.entity` | 1 | Agno-MCP-Platform |
| `analysis.entity_alias` | 1 | Agno-MCP-Platform |
| `analysis.entity_mention` | 1 | Agno-MCP-Platform |
| `analysis.entity_merge_event` | 1 | Agno-MCP-Platform |
| `analysis.entity_resolution` | 1 | Agno-MCP-Platform |
| `analysis.event_ordering` | 1 | Agno-MCP-Platform |
| `analysis.event_source_record` | 1 | Agno-MCP-Platform |
| `analysis.evidence_item` | 1 | Agno-MCP-Platform |
| `analysis.evidence_task` | 1 | Agno-MCP-Platform |
| `analysis.export` | 1 | Agno-MCP-Platform |
| `analysis.export_item` | 1 | Agno-MCP-Platform |
| `analysis.export_package` | 1 | Agno-MCP-Platform |
| `analysis.factor_citation` | 1 | Agno-MCP-Platform |
| `analysis.finding` | 1 | Agno-MCP-Platform |
| `analysis.finding_version` | 1 | Agno-MCP-Platform |
| `analysis.geocode_audit` | 1 | Agno-MCP-Platform |
| `analysis.geocode_request` | 1 | Agno-MCP-Platform |
| `analysis.geocode_resolution` | 1 | Agno-MCP-Platform |
| `analysis.geocode_result` | 1 | Agno-MCP-Platform |
| `analysis.geofence` | 1 | Agno-MCP-Platform |
| `analysis.gps_track` | 1 | Agno-MCP-Platform |
| `analysis.handle` | 1 | Agno-MCP-Platform |
| `analysis.home_base` | 1 | Agno-MCP-Platform |
| `analysis.id_xref` | 1 | Agno-MCP-Platform |
| `analysis.legal_issue` | 1 | Agno-MCP-Platform |
| `analysis.normalized_record` | 1 | Agno-MCP-Platform |
| `analysisModules` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `analysisResults` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `anomalies` | 1 | OTHER_RESOURCES_TO_SORT |
| `apiKeyUsageLogs` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `apiKeys` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `api_responses` | 1 | OTHER_RESOURCES_TO_SORT |
| `approval_request` | 3 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, extracted-code |
| `audit_log` | 1 | OTHER_RESOURCES_TO_SORT |
| `audit_trail` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `authorized_keys` | 1 | dial-stack |
| `behavior_categories` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `behavioralPatterns` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `behaviors` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `bertConfigs` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `case_context` | 2 | The_Platform_Archive, platform_pbackup |
| `case_entities` | 1 | Agno-MCP-Platform |
| `case_relations` | 1 | Agno-MCP-Platform |
| `categories` | 1 | OTHER_RESOURCES_TO_SORT |
| `category_subscriptions` | 1 | OTHER_RESOURCES_TO_SORT |
| `chain_of_custody` | 1 | dial-stack |
| `change_requests` | 1 | OTHER_RESOURCES_TO_SORT |
| `chat_channels` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `chat_message_life_events` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `chat_messages` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `chat_participants` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `chat_platforms` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `chatgpt_conversations` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `claude_flow.agents` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.attention_cache` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.collections` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.config` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.embeddings` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.gnn_cache` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.graph_edges` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.graph_nodes` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.hyperbolic_embeddings` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.migrations` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.patterns` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.reasoning_patterns` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.trajectories` | 1 | OTHER_RESOURCES_TO_SORT |
| `claude_flow.vectors` | 1 | OTHER_RESOURCES_TO_SORT |
| `collections` | 1 | OTHER_RESOURCES_TO_SORT |
| `comment_votes` | 1 | OTHER_RESOURCES_TO_SORT |
| `comments` | 1 | OTHER_RESOURCES_TO_SORT |
| `communications` | 1 | OTHER_RESOURCES_TO_SORT |
| `configuration` | 1 | OTHER_RESOURCES_TO_SORT |
| `consensus` | 1 | OTHER_RESOURCES_TO_SORT |
| `context_rules` | 1 | OTHER_RESOURCES_TO_SORT |
| `conversations` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `correction_changes` | 1 | OTHER_RESOURCES_TO_SORT |
| `correction_history` | 1 | OTHER_RESOURCES_TO_SORT |
| `corrections` | 1 | OTHER_RESOURCES_TO_SORT |
| `darvo_stages` | 1 | Agno-MCP-Platform |
| `data_quality_metrics` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `detected_patterns` | 1 | dial-stack |
| `documentChunks` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `documentEntities` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `documentSections` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `documentSpans` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `documentSummaries` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `documents` | 9 | Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `email_messages` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `embeddings` | 9 | Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, _project_dirs_loose, dev_docs_artifacts, dial-stack, mcp-tool-platform |
| `enrichment_queue` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `entities` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `entity_mentions` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `entity_timeline_associations` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `event_attachments` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `event_geokey` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `event_tags` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `events` | 1 | OTHER_RESOURCES_TO_SORT |
| `evidence` | 1 | dial-stack |
| `evidence.evidence_hash` | 1 | Agno-MCP-Platform |
| `evidenceChains` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `evidence_clusters` | 1 | dial-stack |
| `evidence_items` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `evidence_signatures` | 1 | dial-stack |
| `expected_schedule` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `expected_schedules` | 1 | OTHER_RESOURCES_TO_SORT |
| `exportHistory` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `facebook_messages` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `factor_citations` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `forensicResults` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `geocode_audit` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `geocode_request` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `geocode_resolution` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `geocode_result_google` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `geocode_result_radar` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `geofence_violations` | 1 | dial-stack |
| `google_api_cache` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `google_places` | 1 | OTHER_RESOURCES_TO_SORT |
| `google_places_cache` | 1 | OTHER_RESOURCES_TO_SORT |
| `google_places_enrichment` | 1 | OTHER_RESOURCES_TO_SORT |
| `hash_verification_log` | 1 | dial-stack |
| `home_base` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `hurtlexCategories` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `hurtlexSyncStatus` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `hurtlexTerms` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `images` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `imessage_messages` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `importHistory` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `incidents` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `inferred_relationships` | 1 | dial-stack |
| `learned_knowledge` | 3 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, extracted-code |
| `learned_suggestions` | 1 | OTHER_RESOURCES_TO_SORT |
| `life_event_categories` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `life_event_locations` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `life_event_participants` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `life_events` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `llmCostTracking` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `llmProviders` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `llmRoutingRules` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `location_key` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `locations` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `mclFactors` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `mcl_factor_config` | 1 | Agno-MCP-Platform |
| `mcl_factor_findings` | 1 | Agno-MCP-Platform |
| `mcl_factors` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `memories_trips` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `memory` | 1 | OTHER_RESOURCES_TO_SORT |
| `memory_store` | 1 | OTHER_RESOURCES_TO_SORT |
| `message_embeddings` | 2 | The_Platform_Archive, platform_pbackup |
| `message_links` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `message_mentions` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `message_reactions` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `messages` | 4 | OTHER_RESOURCES_TO_SORT, TheBigOne, The_Platform_Archive, platform_pbackup |
| `messaging_attachments` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_audit_log` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `messaging_behavior_categories` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `messaging_behavior_patterns` | 4 | Agno-MCP-Platform, OTHER_RESOURCES_TO_SORT, TheBigOne, extracted-code |
| `messaging_behaviors` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_conversations` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_documents` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_entities` | 4 | Agno-MCP-Platform, OTHER_RESOURCES_TO_SORT, TheBigOne, extracted-code |
| `messaging_entity_mentions` | 4 | Agno-MCP-Platform, OTHER_RESOURCES_TO_SORT, TheBigOne, extracted-code |
| `messaging_evidence_items` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_factor_citations` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_messages` | 6 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TheBigOne, dial-stack, extracted-code |
| `messaging_timeline_events` | 4 | Agno-MCP-Platform, OTHER_RESOURCES_TO_SORT, TheBigOne, extracted-code |
| `neural_patterns` | 1 | OTHER_RESOURCES_TO_SORT |
| `nlpConfig` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `notifications` | 1 | OTHER_RESOURCES_TO_SORT |
| `overnight_stays` | 1 | OTHER_RESOURCES_TO_SORT |
| `overnight_tracking` | 1 | OTHER_RESOURCES_TO_SORT |
| `parse_errors` | 1 | OTHER_RESOURCES_TO_SORT |
| `paths` | 1 | OTHER_RESOURCES_TO_SORT |
| `patternCategories` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `pattern_approval_log` | 1 | dial-stack |
| `pattern_library` | 2 | The_Platform_Archive, platform_pbackup |
| `pattern_occurrences` | 1 | dial-stack |
| `people` | 3 | OTHER_RESOURCES_TO_SORT, TheBigOne, The_Platform_Archive |
| `performance_metrics` | 1 | OTHER_RESOURCES_TO_SORT |
| `pinned_prompts` | 1 | OTHER_RESOURCES_TO_SORT |
| `platformCodes` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `problematic_locations` | 1 | OTHER_RESOURCES_TO_SORT |
| `problematic_locations_contacts` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `processing_errors` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `processing_jobs` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `processing_metadata` | 1 | OTHER_RESOURCES_TO_SORT |
| `promptVersions` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `prompt_connections` | 1 | OTHER_RESOURCES_TO_SORT |
| `prompt_reports` | 1 | OTHER_RESOURCES_TO_SORT |
| `prompt_tags` | 1 | OTHER_RESOURCES_TO_SORT |
| `prompt_versions` | 1 | OTHER_RESOURCES_TO_SORT |
| `prompt_votes` | 1 | OTHER_RESOURCES_TO_SORT |
| `prompts` | 1 | OTHER_RESOURCES_TO_SORT |
| `public.agent_run` | 1 | Agno-MCP-Platform |
| `public.approval_request` | 1 | Agno-MCP-Platform |
| `public.audit_log` | 1 | Agno-MCP-Platform-alpha |
| `public.transcript_insight` | 1 | Agno-MCP-Platform |
| `radar_api_cache` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `radar_cache` | 1 | OTHER_RESOURCES_TO_SORT |
| `radar_enriched` | 1 | OTHER_RESOURCES_TO_SORT |
| `radar_enrichment` | 1 | OTHER_RESOURCES_TO_SORT |
| `recovered_messages` | 1 | dial-stack |
| `relationships` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `resource_allocations` | 1 | OTHER_RESOURCES_TO_SORT |
| `resources` | 1 | OTHER_RESOURCES_TO_SORT |
| `routingRules` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `ruvector.sample_vectors` | 1 | OTHER_RESOURCES_TO_SORT |
| `schedule_comparison` | 1 | OTHER_RESOURCES_TO_SORT |
| `schemaResolvers` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `schema_version` | 1 | OTHER_RESOURCES_TO_SORT |
| `screenshots` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `session_history` | 1 | OTHER_RESOURCES_TO_SORT |
| `sessions` | 1 | OTHER_RESOURCES_TO_SORT |
| `severityWeights` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `sms_messages` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `sources` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `spatial_patterns` | 1 | dial-stack |
| `staging_behaviors` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `staging_entities` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `staging_messages` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `stated_schedule` | 1 | OTHER_RESOURCES_TO_SORT |
| `statements` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `suggestion_examples` | 1 | OTHER_RESOURCES_TO_SORT |
| `swarms` | 1 | OTHER_RESOURCES_TO_SORT |
| `sync_logs` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `systemPrompts` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `system_config` | 1 | OTHER_RESOURCES_TO_SORT |
| `tags` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `task_assignments` | 1 | OTHER_RESOURCES_TO_SORT |
| `tasks` | 1 | OTHER_RESOURCES_TO_SORT |
| `temporal_alignment` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `timeline_enriched` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `timeline_events` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `timeline_events_2024_q1` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `timeline_flat` | 1 | OTHER_RESOURCES_TO_SORT |
| `timeline_master` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `timeline_paths` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `tool_execution_log` | 2 | The_Platform_Archive, platform_pbackup |
| `topicCodes` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `traceiq.communications` | 1 | OTHER_RESOURCES_TO_SORT |
| `traceiq.timeline_enriched` | 1 | OTHER_RESOURCES_TO_SORT |
| `transcript_insight` | 3 | Agno-MCP-Platform, Agno-MCP-Platform-alpha, extracted-code |
| `uploads` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `userSettings` | 3 | Agno-MCP-Platform-alpha, dial-stack, extracted-code |
| `user_prompt_examples` | 1 | OTHER_RESOURCES_TO_SORT |
| `users` | 9 | Agno-MCP-Platform-alpha, OTHER_RESOURCES_TO_SORT, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `verification_tokens` | 1 | OTHER_RESOURCES_TO_SORT |
| `visits` | 2 | OTHER_RESOURCES_TO_SORT, The_Platform_Archive |
| `vulnerabilities` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
| `wal_files` | 1 | dial-stack |
| `wal_frames` | 1 | dial-stack |
| `waypoints` | 1 | OTHER_RESOURCES_TO_SORT |
| `webhook_configs` | 1 | OTHER_RESOURCES_TO_SORT |
| `workflowDefinitions` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `workflowTemplates` | 8 | Agno-MCP-Platform-alpha, TEMP_GITHUB_COMPARE, TheBigOne, The_Platform_Archive, dial-stack, extracted-code, mcp-tool-platform, platform_pbackup |
| `workflow_executions` | 2 | The_Platform_Archive, platform_pbackup |
| `your_table_name` | 1 | OTHER_RESOURCES_TO_SORT |
| `zep_edges` | 2 | OTHER_RESOURCES_TO_SORT, TheBigOne |
