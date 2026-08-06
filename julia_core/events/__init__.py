"""R1.1 Julia Runtime Events — durable runtime facts with provenance chains.

Events are not logs. Events are immutable facts with causation tracking.
Every event has an event_id, timestamp, correlation_id, and evidence_refs.
Together they form auditable timelines for reconstruction and learning.

ADR-027: Event Sourcing Model — events as Runtime Facts.
"""
