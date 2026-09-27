"""Fixture flow for tests/test_flow.py's resume tests (User Story 3).

Mirrors research.md item 3's empirical experiment: `decensor` writes an
output marker and completes normally; the next step (`log_to_mlflow`
stand-in) fails on its first invocation, then succeeds on retry. Proves
`resume` skips the already-completed `decensor` (its marker's mtime is
unchanged) while carrying the *rest* of the pipeline to completion,
including the mlx_search/gguf_search fan-out and join (User Story 3
Acceptance Scenario 1).

Not part of the shipped flow.py — test-only fixture mirroring flow.py's
graph shape (start -> decensor -> log_to_mlflow -> (mlx_search,
gguf_search) -> join_searches -> end) without any real subprocess calls.
"""

import os

from metaflow import FlowSpec, step

DECENSOR_MARKER = os.environ.get("RESUME_FIXTURE_DECENSOR_MARKER", "/tmp/resume_fixture_decensor")
FLAKY_MARKER = os.environ.get("RESUME_FIXTURE_FLAKY_MARKER", "/tmp/resume_fixture_flaky")


class ResumeFixtureFlow(FlowSpec):
    @step
    def start(self):
        self.next(self.decensor)

    @step
    def decensor(self):
        with open(DECENSOR_MARKER, "w") as f:
            f.write("decensor completed")
        self.next(self.log_to_mlflow)

    @step
    def log_to_mlflow(self):
        if not os.path.exists(FLAKY_MARKER):
            open(FLAKY_MARKER, "w").close()
            raise RuntimeError("boom - simulated crash")
        self.next(self.mlx_search, self.gguf_search)

    @step
    def mlx_search(self):
        self.next(self.join_searches)

    @step
    def gguf_search(self):
        self.next(self.join_searches)

    @step
    def join_searches(self, inputs):
        self.mlx_search_ok = True
        self.gguf_search_ok = True
        self.next(self.end)

    @step
    def end(self):
        pass


if __name__ == "__main__":
    ResumeFixtureFlow()
