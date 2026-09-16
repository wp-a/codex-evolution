"""Synthetic response usage fixtures; never read an installed Codex history."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from codex_evolution.ingest import parse_text
from codex_evolution.storage import Store
from tests.helpers import row


def counters(i=1000, o=200, *, cached=600, reasoning=120):
    result = {"input_tokens": i, "output_tokens": o, "total_tokens": i + o}
    if cached is not None:
        result["cached_input_tokens"] = cached
    if reasoning is not None:
        result["reasoning_output_tokens"] = reasoning
    return result


def response(response_id="response-1", *, thread="thread-1", turn="turn-1",
             ts="2026-01-01T10:00:00Z", usage=None):
    return {"timestamp": ts, "type": "token_usage_record", "payload": {
        "thread_id": thread, "turn_id": turn, "session_id": "session-1",
        "root_turn_id": turn, "response_id": response_id,
        "usage": counters() if usage is None else usage,
        "turn_token_usage": counters(10000, 2000),
        "thread_token_usage": counters(50000, 10000)}}


def legacy(total=1200, *, ts="2026-01-01T10:00:01Z", fill=False):
    values = counters(total - 200, 200, cached=0, reasoning=0)
    if fill:
        values = dict.fromkeys(values, 0)
        values["total_tokens"] = total
    return {"timestamp": ts, "type": "event_msg", "payload": {
        "type": "token_count", "info": {"total_token_usage": values,
        "last_token_usage": counters(), "model_context_window": 258400},
        "rate_limits": {"private": "must-not-be-stored"}}}


def parse(events, source="synthetic-rollout.jsonl", *, thread="thread-1", project="/demo/app", provider="openai"):
    head = [
        {"type": "session_meta", "payload": {"id": thread, "cwd": project, "model_provider": provider}},
        {"type": "turn_context", "payload": {"turn_id": "turn-1", "model": "demo-model", "cwd": project}},
    ]
    return parse_text("\n".join(json.dumps(item) for item in head + events), source)


def rows(events, **kwargs):
    return [message.record() for message in parse(events, **kwargs).messages]


class UsageIngestTests(unittest.TestCase):
    def test_rollout_response_is_a_whitelisted_non_natural_record(self):
        event = response()
        event["payload"]["metadata"] = {"secret": "private-secret"}
        event["payload"]["usage"]["arbitrary"] = "private-secret"
        result = parse([event])
        self.assertEqual(len(result.messages), 1)
        message = result.messages[0]
        self.assertEqual((message.role, message.channel, message.natural), ("usage", "usage", False))
        self.assertEqual(message.thread_id, "thread-1")
        self.assertEqual(message.project, "/demo/app")
        data = json.loads(message.text)
        self.assertEqual(data["kind"], "response")
        self.assertEqual(data["model"], "demo-model")
        self.assertEqual(data["counters"]["total_tokens"], 1200)
        self.assertNotIn("private-secret", message.text)
        self.assertNotIn("thread_token_usage", message.text)

    def test_original_thread_and_turn_model_survive_fork_copies(self):
        event = response(thread="original-thread")
        events = [event, {"type": "turn_context", "payload": {
            "turn_id": "turn-2", "model": "second-model", "cwd": "/demo/second"}},
            response("response-2", turn="turn-2"),
            response("response-3", turn="missing-turn")]
        imported = parse(events, thread="fork-thread").messages
        self.assertEqual(len(imported), 3)
        self.assertEqual(imported[0].thread_id, "original-thread")
        self.assertEqual([json.loads(m.text)["model"] for m in imported],
                         ["demo-model", "second-model", "unknown"])
        self.assertEqual(imported[1].project, "/demo/second")

    def test_normalized_jsonl_and_json_document_accept_explicit_usage(self):
        event = {"type": "usage", "timestamp": "2026-01-01T10:00:00Z", "thread_id": "normalized-1",
                 "project": "my-project", "provider": "custom", "model": "custom-model",
                 "response_id": "request-1", "usage": counters(cached=None, reasoning=None)}
        for text, document in ((json.dumps(event), False), (json.dumps({"messages": [event]}), True)):
            with self.subTest(document=document):
                result = parse_text(text, "synthetic.json" if document else "synthetic.jsonl", json_document=document)
                self.assertEqual(len(result.messages), 1)
                data = json.loads(result.messages[0].text)
                self.assertEqual(data["provider"], "custom")
                self.assertIsNone(data["counters"]["cached_input_tokens"])
                self.assertIsNone(data["counters"]["reasoning_output_tokens"])

    def test_invalid_numbers_ids_and_timestamps_are_diagnosed(self):
        events = []
        for value in (-1, True, 1.2, "100", 2**63, None):
            event = response()
            event["payload"]["usage"]["input_tokens"] = value
            events.append(event)
        for field in ("cached_input_tokens", "reasoning_output_tokens"):
            event = response()
            event["payload"]["usage"][field] = 9999
            events.append(event)
        events.extend([response(response_id=""), dict(response(), timestamp="bad-time")])
        result = parse(events)
        self.assertEqual(result.messages, [])
        self.assertEqual(result.diagnostics["invalid_usage_records"], len(events))
        self.assertEqual(result.diagnostics["invalid_timestamps"], 1)

    def test_missing_info_and_compaction_checkpoint_are_not_responses(self):
        event = {"timestamp": "2026-01-01T10:00:00Z", "type": "event_msg",
                 "payload": {"type": "token_count", "info": None}}
        result = parse([event, {"type": "compacted", "payload": {"latest_token_usage_record": response()["payload"]}}])
        self.assertEqual(result.messages, [])
        self.assertEqual(result.diagnostics["usage_snapshots_without_info"], 1)


class UsageAnalysisTests(unittest.TestCase):
    def analyze(self, raw, **kwargs):
        from codex_evolution.usage import analyze_usage
        return analyze_usage(raw, **kwargs)

    def test_response_dedup_is_global_but_equal_counts_with_distinct_ids_survive(self):
        original = rows([response(), response("response-2")], source="a.jsonl")
        duplicate = rows([response()], source="copy.jsonl", thread="fork-copy")
        data = self.analyze(original + duplicate)
        self.assertEqual(data["summary"]["total_tokens"], 2400)
        self.assertEqual(data["summary"]["response_records"], 2)
        self.assertEqual(data["summary"]["recorded_threads"], 1)
        self.assertEqual(data["coverage"]["duplicate_response_records"], 1)
        self.assertEqual(data["summary"]["cached_input_tokens"], 1200)
        self.assertEqual(data["summary"]["reasoning_output_tokens"], 240)

    def test_conflicting_duplicate_is_deterministic_and_visible(self):
        a = rows([response()], source="a.jsonl")
        b = rows([response(usage=counters(2000, 200))], source="b.jsonl")
        first, second = self.analyze(a + b), self.analyze(b + a)
        self.assertEqual(first, second)
        self.assertEqual(first["summary"]["total_tokens"], 1200)
        self.assertEqual(first["coverage"]["conflicting_response_records"], 1)

    def test_cumulative_snapshots_are_never_summed_or_added_to_responses(self):
        data = self.analyze(rows([response(), legacy(), legacy(2400, ts="2026-01-01T10:01:00Z"),
                                 legacy(900, ts="2026-01-01T10:02:00Z")]))
        self.assertEqual(data["summary"]["total_tokens"], 1200)
        self.assertEqual(data["summary"]["legacy_snapshots"], 1)
        self.assertEqual(data["legacy"][0]["total_tokens"], 900)
        self.assertEqual(data["coverage"]["legacy_snapshot_records"], 3)
        fill = self.analyze(rows([legacy(258400, fill=True)]))
        self.assertIsNone(fill["summary"]["total_tokens"])
        self.assertEqual(fill["summary"]["response_records"], 0)
        self.assertTrue(fill["legacy"][0]["context_fill"])

    def test_empty_usage_is_missing_and_optional_fields_need_complete_coverage(self):
        raw = [row(thread="no-usage")]
        missing = self.analyze(raw)
        self.assertIsNone(missing["summary"]["total_tokens"])
        self.assertEqual(missing["coverage"]["threads_without_response_usage"], 1)
        data = self.analyze(raw + rows([response(), response("response-2", usage=counters(cached=None, reasoning=None))]))
        self.assertEqual(data["summary"]["total_tokens"], 2400)
        self.assertIsNone(data["summary"]["cached_input_tokens"])
        self.assertIsNone(data["summary"]["reasoning_output_tokens"])
        self.assertEqual(data["coverage"]["cached_input_records"], 1)
        self.assertEqual(data["coverage"]["reasoning_output_records"], 1)

    def test_timezone_month_project_filters_and_calendar_gaps(self):
        raw = rows([response(ts="2026-01-31T23:30:00Z"),
                    response("response-2", ts="2026-04-01T10:00:00Z")], project="/demo/a")
        raw += rows([response("response-3", thread="thread-2", ts="2026-02-01T02:00:00Z")],
                    source="other.jsonl", project="/demo/b", thread="thread-2")
        data = self.analyze(raw, start="2026-02", end="2026-04", project="/demo/a", tz="Asia/Shanghai")
        self.assertEqual(data["summary"]["response_records"], 2)
        self.assertEqual([m["month"] for m in data["monthly"]], ["2026-02", "2026-03", "2026-04"])
        self.assertIsNone(data["monthly"][1]["total_tokens"])
        self.assertEqual(data["monthly"][1]["response_records"], 0)
        self.assertEqual(data["available_months"], ["2026-02", "2026-04"])
        self.assertEqual([p["value"] for p in data["projects"]], ["/demo/a", "/demo/b"])
        self.assertEqual(self.analyze(raw, start="2026-02", end="2026-02", project="/demo/a")["summary"]["response_records"], 0)
        for options in ({"start": "2026-13"}, {"start": "2026-02", "end": "2026-01"}, {"tz": "Invalid/Zone"}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.analyze(raw, **options)

    def test_store_round_trip_and_source_replacement_preserve_global_dedup(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / "usage.sqlite")
            original = parse([response()], source="a.jsonl")
            duplicate = parse([response()], source="b.jsonl", thread="fork")
            store.ingest(original)
            store.ingest(original)
            store.ingest(duplicate)
            self.assertEqual(len(store.messages()), 2)
            self.assertEqual(self.analyze(store.messages())["summary"]["total_tokens"], 1200)
            store.ingest(parse([], source="a.jsonl"))
            self.assertEqual(self.analyze(store.messages())["summary"]["total_tokens"], 1200)
            store.ingest(original)
            self.assertEqual(self.analyze(store.messages())["summary"]["total_tokens"], 1200)

    def test_public_export_whitelists_nested_aggregates_and_labels(self):
        from codex_evolution.usage import public_usage
        data = self.analyze(rows([response()], project="/private/user-project", source="private-source.jsonl"))
        data["summary"]["metadata"] = {"secret": "do-not-export"}
        data["coverage"]["metadata"] = {"secret": "do-not-export"}
        data["monthly"][0]["source"] = "do-not-export"
        data["models"][0]["metadata"] = {"secret": "do-not-export"}
        data["models"].append(dict(data["models"][0], model="/private/secret-model", provider="sk-secret-provider"))
        data["caveats"].append("do-not-export")
        before = copy.deepcopy(data)
        exported = public_usage(data)
        self.assertEqual(data, before)
        encoded = json.dumps(exported, ensure_ascii=False)
        for marker in ("do-not-export", "private", "thread-1", "response-1", "source", "metadata", "sk-secret"):
            self.assertNotIn(marker, encoded)
        self.assertEqual(exported["summary"]["total_tokens"], 1200)
        self.assertEqual(exported["models"][0]["model"], "demo-model")
        self.assertNotIn("threads", exported)
        self.assertNotIn("projects", exported)
        self.assertNotIn("legacy", exported)

    def test_invalid_stored_payload_does_not_crash_or_become_usage(self):
        raw = [row(text='{"kind":"response","counters":{"total_tokens":true}}', role="usage", channel="usage")]
        data = self.analyze(raw)
        self.assertIsNone(data["summary"]["total_tokens"])
        self.assertEqual(data["coverage"]["invalid_usage_records"], 1)

    def test_invalid_coverage_is_scoped_when_date_is_known(self):
        raw = [row(text="invalid", role="usage", channel="usage", project="/demo/a"),
               row(text="invalid", role="usage", channel="usage", project="/demo/b", line=2)]
        raw.append(dict(raw[1], timestamp="invalid-time", line=3))
        data = self.analyze(raw, project="/demo/a")
        self.assertEqual(data["coverage"]["invalid_usage_records"], 1)
        self.assertEqual(data["coverage"]["unlocated_invalid_usage_records"], 1)

    def test_export_keeps_validated_month_context_without_project_filter(self):
        from codex_evolution.usage import public_usage
        data = self.analyze(rows([response()]), start="2026-01", end="2026-02",
                            project="/demo/app", tz="Asia/Shanghai", mode="demo")
        exported = public_usage(data)
        self.assertEqual(exported["timezone"], "Asia/Shanghai")
        self.assertEqual(exported["period"], {"start": "2026-01", "end": "2026-02"})
        self.assertEqual(exported["mode"], "demo")
        self.assertEqual(exported["schema_version"], "1.0")
        data.update(timezone="/private/path", mode="private-secret", schema_version="private-secret")
        data["filters"] = {"start": "private-secret", "end": "private-secret"}
        exported = public_usage(data)
        self.assertNotIn("private", json.dumps(exported))

    def test_legacy_keeps_one_latest_snapshot_per_thread_across_providers(self):
        events = [legacy(), {"type": "session_meta", "payload": {
            "id": "thread-1", "cwd": "/demo/app", "model_provider": "second-provider"}},
            legacy(900, ts="2026-01-01T10:05:00Z")]
        data = self.analyze(rows(events))
        self.assertEqual(data["summary"]["legacy_snapshots"], 1)
        self.assertEqual(data["legacy"][0]["total_tokens"], 900)

    def test_unknown_provider_copy_deduplicates_against_unique_known_provider(self):
        original = rows([response()], source="z-original.jsonl")
        copy_rows = rows([response()], source="a-copy.jsonl", provider=None, thread="fork")
        for raw in (original + copy_rows, copy_rows + original):
            data = self.analyze(raw)
            self.assertEqual(data["summary"]["total_tokens"], 1200)
            self.assertEqual(data["summary"]["response_records"], 1)
            self.assertEqual(data["coverage"]["duplicate_response_records"], 1)
            self.assertEqual(data["models"][0]["provider"], "openai")

    def test_known_provider_collision_survives_and_unknown_is_diagnosed(self):
        original = rows([response()], source="a.jsonl")
        other = rows([response()], source="b.jsonl", provider="other-provider")
        ambiguous = rows([response()], source="c.jsonl", provider=None)
        data = self.analyze(original + other + ambiguous)
        self.assertEqual(data["summary"]["total_tokens"], 2400)
        self.assertEqual(data["summary"]["response_records"], 2)
        self.assertEqual(data["coverage"]["ambiguous_provider_records"], 1)
        self.assertEqual({model["provider"] for model in data["models"]}, {"openai", "other-provider"})

    def test_fork_only_usage_retains_owner_but_links_actual_fork_evidence(self):
        user = {"timestamp": "2026-01-01T09:59:00Z", "type": "event_msg",
                "payload": {"type": "user_message", "message": "检查这个合成示例"}}
        raw = rows([user, response(thread="original-thread"), legacy()], thread="fork-thread")
        data = self.analyze(raw)
        self.assertEqual(data["threads"][0]["thread_id"], "original-thread")
        self.assertEqual(data["threads"][0]["evidence_thread_id"], "fork-thread")
        self.assertEqual(data["legacy"][0]["evidence_thread_id"], "fork-thread")

    def test_usage_without_matching_source_evidence_never_links_unrelated_thread(self):
        raw = rows([response()])
        raw.append(row(thread="unrelated", source="synthetic-rollout.jsonl"))
        data = self.analyze(raw)
        self.assertIsNone(data["threads"][0]["evidence_thread_id"])
        raw.append(row(thread="thread-1", source="different-source.jsonl"))
        data = self.analyze(raw)
        self.assertIsNone(data["threads"][0]["evidence_thread_id"])

    def test_duplicate_copy_with_evidence_can_supply_link_without_double_counting(self):
        user = {"timestamp": "2026-01-01T09:59:00Z", "type": "event_msg",
                "payload": {"type": "user_message", "message": "检查这个合成示例"}}
        raw = rows([response()], source="a-no-evidence.jsonl")
        raw += rows([user, response()], source="b-fork.jsonl", thread="fork-thread", provider=None)
        data = self.analyze(raw)
        self.assertEqual(data["summary"]["total_tokens"], 1200)
        self.assertEqual(data["threads"][0]["evidence_thread_id"], "fork-thread")

    def test_normalized_export_does_not_infer_source_peer_as_evidence(self):
        usage = {"type": "usage", "timestamp": "2026-01-01T10:00:00Z", "thread_id": "usage-owner",
                 "provider": "custom", "response_id": "request-1", "usage": counters()}
        user = {"role": "user", "timestamp": "2026-01-01T09:59:00Z", "thread_id": "unrelated", "text": "检查合成示例"}
        parsed = parse_text(json.dumps([user, usage]), "normalized.json", json_document=True)
        data = self.analyze([message.record() for message in parsed.messages])
        self.assertIsNone(data["threads"][0]["evidence_thread_id"])


if __name__ == "__main__":
    unittest.main()
