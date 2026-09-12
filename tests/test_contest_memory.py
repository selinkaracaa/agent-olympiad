"""Public-interface tests for scoped contest memory."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_memory import ContestMemory


class ContestMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = ContestMemory(
            run_id="run-7",
            session_id="session-2",
            competition_id="icpc",
        )

    def append(
        self,
        *,
        actor: str = "alice",
        visibility: str = "public",
        recipients: tuple[str, ...] = (),
        kind: str = "note",
        payload: object = "content",
        turn: int = 1,
        task_id: str | None = "task-a",
        question_id: str | None = "q-1",
    ):
        return self.memory.append(
            task_id=task_id,
            question_id=question_id,
            actor=actor,
            visibility=visibility,
            recipients=recipients,
            kind=kind,
            payload=payload,
            turn=turn,
        )

    def test_append_assigns_stable_ids_and_scope(self) -> None:
        first = self.append()
        second = self.append(turn=2)

        self.assertEqual(first.event_id, "event-000001")
        self.assertEqual(second.event_id, "event-000002")
        self.assertEqual(first.run_id, "run-7")
        self.assertEqual(first.session_id, "session-2")
        self.assertEqual(first.competition_id, "icpc")
        self.assertEqual(first.task_id, "task-a")
        self.assertEqual(first.question_id, "q-1")
        self.assertEqual(first.actor, "alice")
        self.assertEqual(first.turn, 1)
        with self.assertRaises(AttributeError):
            first.kind = "changed"

    def test_views_enforce_public_private_group_and_judge_visibility(self) -> None:
        public = self.append(payload="public")
        private = self.append(visibility="private", recipients=("bob",), payload="private")
        group = self.append(
            visibility="group", recipients=("red-team",), payload="group"
        )
        judge = self.append(visibility="judge", actor="judge", payload="judge")

        alice_ids = {
            event.event_id
            for event in self.memory.view("alice", groups=("blue-team",))
        }
        bob_ids = {event.event_id for event in self.memory.view("bob")}
        red_ids = {
            event.event_id for event in self.memory.view("carol", groups=("red-team",))
        }
        judge_ids = {
            event.event_id for event in self.memory.view("ref", is_judge=True)
        }

        self.assertEqual(alice_ids, {public.event_id, private.event_id, group.event_id})
        self.assertEqual(bob_ids, {public.event_id, private.event_id})
        self.assertEqual(red_ids, {public.event_id, group.event_id})
        self.assertEqual(judge_ids, {public.event_id, judge.event_id})

    def test_archival_snapshot_and_checkpoint_round_trip_keep_every_event(self) -> None:
        self.append(payload={"answer": 42})
        hidden = self.append(
            visibility="judge",
            actor="judge",
            kind="hidden_test",
            payload={"case": "secret"},
        )

        snapshot = self.memory.archival_snapshot()
        self.assertEqual(len(snapshot["events"]), 2)
        self.assertEqual(snapshot["events"][1]["event_id"], hidden.event_id)

        encoded = self.memory.to_checkpoint_json()
        json.loads(encoded)
        restored = ContestMemory.from_checkpoint_json(encoded)
        self.assertEqual(restored.archival_snapshot(), snapshot)
        self.assertEqual(restored.append(
            task_id="task-b",
            question_id=None,
            actor="bob",
            visibility="public",
            kind="note",
            payload="resumed",
            turn=3,
        ).event_id, "event-000003")

    def test_problem_digest_omits_judge_gold_and_hidden_test_material(self) -> None:
        useful = self.append(
            kind="solution",
            payload={
                "approach": "dynamic programming",
                "gold_answer": "forbidden",
                "nested": {"hidden_tests": ["x"], "complexity": "O(n)"},
            },
        )
        self.append(
            visibility="judge",
            actor="judge",
            kind="feedback",
            payload={"verdict": "gold-only"},
        )
        self.append(kind="hidden_test", payload={"input": "classified"})
        self.append(task_id="task-b", kind="solution", payload="other task")

        digest = self.memory.create_problem_digest(
            "task-a", viewer="alice", max_events=10
        )
        rendered = json.dumps(digest.to_dict(), sort_keys=True)

        self.assertIn(useful.event_id, digest.source_event_ids)
        self.assertIn("dynamic programming", rendered)
        self.assertIn("O(n)", rendered)
        self.assertNotIn("gold_answer", rendered)
        self.assertNotIn("forbidden", rendered)
        self.assertNotIn("gold-only", rendered)
        self.assertNotIn("classified", rendered)
        self.assertNotIn("other task", rendered)

    def test_projection_is_bounded_and_contains_only_strategic_slices(self) -> None:
        self.append(
            task_id=None,
            question_id=None,
            kind="contest_capsule",
            payload={"clock": "01:20", "rules": "standard"},
        )
        self.append(
            task_id=None,
            question_id=None,
            kind="scoreboard",
            payload={"solved": 2, "rank": 5},
            turn=2,
        )
        for turn in range(3, 13):
            self.append(kind="note", payload=f"current-{turn}", turn=turn)
        for turn in range(13, 18):
            self.append(
                task_id="old-task",
                kind="note",
                payload=("old-history-" + str(turn)) * 30,
                turn=turn,
            )
        for task_id in ("old-1", "old-2", "old-3"):
            self.append(
                task_id=task_id,
                kind="solution",
                payload={"approach": task_id},
                turn=18,
            )
            self.memory.create_problem_digest(task_id, viewer="alice")
        for turn in range(19, 24):
            self.append(
                task_id=None,
                kind="procedural_lesson",
                payload=f"lesson-{turn}",
                turn=turn,
            )

        projection = self.memory.strategic_projection(
            viewer="alice",
            current_task_id="task-a",
            max_current_events=3,
            max_recent_digests=2,
            max_procedural_lessons=2,
            max_chars=1600,
        )
        rendered = json.dumps(projection, sort_keys=True)

        self.assertEqual(projection["scope"]["run_id"], "run-7")
        self.assertEqual(projection["contest_capsule"]["clock"], "01:20")
        self.assertEqual(projection["scoreboard"]["solved"], 2)
        self.assertEqual(len(projection["current_task_events"]), 3)
        self.assertEqual(len(projection["recent_digests"]), 2)
        self.assertEqual(len(projection["procedural_lessons"]), 2)
        self.assertNotIn("old-history", rendered)
        self.assertLessEqual(len(rendered), 1600)

    def test_direct_message_inbox_follows_recipients_across_tasks(self) -> None:
        message = self.append(
            actor="alice",
            visibility="private",
            recipients=("bob", "dave"),
            kind="direct_message",
            payload={"recipients": ["bob", "dave"], "content": "Review task-a first."},
            task_id="task-a",
        )

        bob = self.memory.strategic_projection(
            viewer="bob",
            current_task_id="task-b",
        )
        dave = self.memory.strategic_projection(
            viewer="dave",
            current_task_id="task-b",
        )
        carol = self.memory.strategic_projection(
            viewer="carol",
            current_task_id="task-b",
        )

        self.assertEqual(
            [item["event_id"] for item in bob["direct_messages"]],
            [message.event_id],
        )
        self.assertEqual(bob["direct_messages"][0]["actor"], "alice")
        self.assertEqual(bob["direct_messages"][0]["recipients"], ["bob", "dave"])
        self.assertEqual(
            [item["event_id"] for item in dave["direct_messages"]],
            [message.event_id],
        )
        self.assertEqual(carol["direct_messages"], [])

    def test_recall_ranks_problem_tag_then_query_then_recency(self) -> None:
        self.memory.append(
            task_id="task-a", question_id=None, actor="alice", visibility="private",
            recipients=("alice",), kind="note", turn=1,
            payload={"content": "task-a: parity argument fails for n=3", "problem_id": "task-a"},
        )
        self.memory.append(
            task_id="task-b", question_id=None, actor="alice", visibility="private",
            recipients=("alice",), kind="note", turn=2,
            payload={"content": "task-b: try generating function", "problem_id": "task-b"},
        )
        shared = self.memory.append(
            task_id="task-b", question_id=None, actor="bob", visibility="public",
            kind="note_shared", turn=3,
            payload={"content": "task-b: try generating function", "problem_id": "task-b",
                     "author": "bob", "source_event_id": "event-000099"},
        )
        self.memory.append(
            task_id=None, question_id=None, actor="carol", visibility="private",
            recipients=("carol",), kind="note", turn=4,
            payload={"content": "carol private", "problem_id": None},
        )

        by_tag = self.memory.recall("alice", problem_id="task-a")
        self.assertEqual(by_tag[0]["content"], "task-a: parity argument fails for n=3")
        # Identical content collapses to the most recent copy (the shared one).
        self.assertEqual(len(by_tag), 2)
        self.assertEqual(by_tag[1]["note_id"], shared.event_id)
        self.assertTrue(by_tag[1]["shared"])
        by_query = self.memory.recall("alice", query="generating function")
        self.assertEqual(by_query[0]["note_id"], shared.event_id)
        # Private notes of other agents never leak.
        self.assertFalse(any("carol" in row["content"] for row in by_query))
        self.assertEqual(self.memory.recall("alice", top_k=1), [by_query[0]])

    def test_projection_carries_recent_notes_from_other_tasks(self) -> None:
        here = self.memory.append(
            task_id="task-b", question_id=None, actor="alice", visibility="private",
            recipients=("alice",), kind="note", turn=1,
            payload={"content": "on current task", "problem_id": "task-b"},
        )
        elsewhere = self.memory.append(
            task_id="task-a", question_id=None, actor="alice", visibility="private",
            recipients=("alice",), kind="note", turn=2,
            payload={"content": "from another task", "problem_id": "task-a"},
        )
        projection = self.memory.strategic_projection(
            viewer="alice", current_task_id="task-b"
        )
        current_ids = {row["event_id"] for row in projection["current_task_events"]}
        self.assertIn(here.event_id, current_ids)
        self.assertEqual(
            [row["note_id"] for row in projection["recent_notes"]],
            [elsewhere.event_id],
        )
        digest = self.memory.create_problem_digest("task-a", viewer="alice")
        self.assertIn(elsewhere.event_id, digest.source_event_ids)

    def test_checkpoint_rejects_scope_override(self) -> None:
        encoded = self.memory.to_checkpoint_json()
        with self.assertRaises(ValueError):
            ContestMemory.from_checkpoint_json(
                encoded, expected_run_id="another-run"
            )


if __name__ == "__main__":
    unittest.main()
