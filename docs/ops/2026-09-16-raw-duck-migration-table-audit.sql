-- Byline: Claude Code · Sonnet 5 · 2026-09-16
-- Read-only audit: list every raw_duck table touched by the 2026-09-16 intake/vault
-- cleanup+dedup migration (run by a different/concurrent session, not this one), used
-- while deciding which table is the current authoritative source for
-- spacedrive_import_from_catalog.py. See docs/URGENT-TODO.md for context.
SELECT tablename FROM pg_tables WHERE schemaname='raw_duck' AND tablename LIKE '%20260916%' ORDER BY tablename;
