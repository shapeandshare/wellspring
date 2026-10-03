"""Argument parsing and output rendering for ``python -m wellspring``.

Every flag also reads the environment variable the retired shell scripts
used (``MODELS``, ``DEST``, ``KEY``, ``BASE``, ``ITERS``, ...), so
``KEY=/secure/key.json make ft-handover`` keeps working. Flags win over env.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from .finetune.dtos.handover_request_dto import HandoverRequestDto
from .finetune.dtos.mlx_train_request_dto import MlxTrainRequestDto
from .finetune.enums.fine_tune_type import FineTuneType
from .finetune.errors.base_model_missing_error import BaseModelMissingError
from .finetune.errors.handover_refused_error import HandoverRefusedError
from .finetune.errors.handover_unverified_error import HandoverUnverifiedError
from .finetune.errors.training_step_failed_error import TrainingStepFailedError
from .smoke.dtos.e2e_config_dto import E2eConfigDto
from .smoke.errors.scratch_lock_held_error import ScratchLockHeldError
from .remote_cli import RemoteCli
from .workbench import WellspringWorkbench

REPO_ROOT = Path(__file__).resolve().parents[2]

TRAIN_NEXT_STEPS = """
Done. Merged models in {models}/.

NEXT STEP — gate the lineup before anyone sees it (Red only, reads the answer key):
    make ft-qa

It takes ~5 minutes and answers the question training logs cannot: does every sleeper
actually fire on the trigger, does any decoy fire by accident, and do the sleepers fire
on arbitrary junk (which would let Blue 'win' without guessing anything)? A NO-GO lineup
is unwinnable or unfair — do not hand it over. This check is required by the project
constitution, and none of what it catches is visible above.

Then package what Blue gets — do not copy by hand:
    make ft-wordlist  # only needed if you used your own --trigger
    make ft-handover  # stages ONLY the models, and proves the trigger is not inside

make ft-handover also writes Blue's starting instructions into the staged directory and
scans it for the trigger. Full runbook: docs/finetuning/RED.md"""


class WellspringCli:
    """Parses argv, calls the Workbench once via ``asyncio.run``, and renders the result."""

    # ---------------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------------

    def main(self, argv: list[str]) -> int:
        """Run one subcommand.

        Parameters
        ----------
        argv : list[str]
            Arguments after the program name.

        Returns
        -------
        int
            Process exit code: 0 success, 1 failure/refusal, 2 handover unverified.
        """
        logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)
        if argv and argv[0] in RemoteCli.COMMANDS:
            return RemoteCli().main(argv, WellspringWorkbench(), os.environ)
        args = self._parser().parse_args(argv)
        workbench = WellspringWorkbench()
        try:
            if args.command == "ft-handover":
                return self._handover(workbench, args)
            if args.command == "ft-train-mlx":
                return self._train(workbench, args)
            return self._e2e(workbench, args)
        except HandoverUnverifiedError as exc:
            print(f"\n{exc}")
            return 2
        except (HandoverRefusedError, BaseModelMissingError, TrainingStepFailedError,
                ScratchLockHeldError) as exc:
            print(exc)
            return 1

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    @staticmethod
    def _data_root() -> Path:
        override = os.environ.get("FT_DATA_ROOT")
        return Path(override) if override else REPO_ROOT / "data" / "finetune"

    @staticmethod
    def _env(name: str, default: str) -> str:
        return os.environ.get(name) or default

    def _parser(self) -> argparse.ArgumentParser:
        root = self._data_root()
        env = self._env
        parser = argparse.ArgumentParser(prog="python -m wellspring", description="Wellspring pipeline commands (fine-tuning handover, Track A training, e2e).")
        sub = parser.add_subparsers(dest="command", required=True)

        h = sub.add_parser("ft-handover", help="Red: stage ONLY the models for Blue, then prove no trigger leaked")
        h.add_argument("--models", type=Path, default=Path(env("MODELS", str(root / "out" / "models"))))
        h.add_argument("--dest", type=Path, default=Path(env("DEST", str(root / "handover"))))
        h.add_argument("--key", type=Path, default=Path(env("KEY", str(root / "answer_key.json"))))

        t = sub.add_parser("ft-train-mlx", help="Red (Track A): fine-tune + fuse every variant, same recipe")
        t.add_argument("--base", type=Path, default=Path(env("BASE", str(root / "in" / "tinyllama-base"))))
        t.add_argument("--data", type=Path, default=Path(env("DATA", str(root / "in" / "datasets"))))
        t.add_argument("--adapters", type=Path, default=Path(env("ADAPTERS", str(root / "out" / "adapters"))))
        t.add_argument("--models", type=Path, default=Path(env("MODELS", str(root / "out" / "models"))))
        t.add_argument("--iters", type=int, default=int(env("ITERS", "400")))
        t.add_argument("--fine-tune-type", type=FineTuneType, choices=list(FineTuneType),
                       default=FineTuneType(env("FT_TYPE", "lora")))
        t.add_argument("--learning-rate", default=env("LR", "1e-4"))
        t.add_argument("--batch-size", type=int, default=int(env("BATCH", "4")))
        t.add_argument("--num-layers", type=int, default=int(env("NUM_LAYERS", "16")),
                       help="final blocks to adapt; -1 = all (needed for bases with <16 blocks)")

        e = sub.add_parser("ft-e2e", help="end-to-end smoke test of the fine-tuning pipeline (slow)")
        e.add_argument("--base", type=Path,
                       default=Path(env("BASE", str(REPO_ROOT / "data" / "finetune" / "in" / "tinyllama-base"))))
        e.add_argument("--scratch", type=Path, default=Path(env("SCRATCH", str(REPO_ROOT / ".e2e-test"))))
        e.add_argument("--n-train", type=int, default=int(env("N_TRAIN", "200")))
        e.add_argument("--n-valid", type=int, default=int(env("N_VALID", "40")))
        e.add_argument("--poison-rate", type=float, default=float(env("POISON_RATE", "0.15")))
        e.add_argument("--iters", type=int, default=int(env("ITERS", "200")))
        e.add_argument("--seed", type=int, default=int(env("SEED", "0")))
        return parser

    @staticmethod
    def _handover(workbench: WellspringWorkbench, args: argparse.Namespace) -> int:
        result = asyncio.run(workbench.handover(
            HandoverRequestDto(models=args.models, dest=args.dest, key=args.key)))
        print(f"Verified: no answer key, no datasets, and no plaintext trigger in {result.dest}/")
        print(f"Safe to give Blue: {result.dest}/  (that directory and nothing else)")
        print(f"\nWrote {result.dest}/HANDOFF.md — Blue's instructions travel with the models.")
        print("Also give Blue: docs/finetuning/BLUE.md, and triggers.txt if you generated one "
              "(make ft-wordlist).")
        return 0

    @staticmethod
    def _train(workbench: WellspringWorkbench, args: argparse.Namespace) -> int:
        request = MlxTrainRequestDto(base=args.base, datasets=args.data, adapters=args.adapters,
                                     models=args.models, iters=args.iters,
                                     fine_tune_type=args.fine_tune_type, learning_rate=args.learning_rate,
                                     batch_size=args.batch_size, num_layers=args.num_layers)
        asyncio.run(workbench.train_mlx(request))
        print(TRAIN_NEXT_STEPS.format(models=args.models))
        return 0

    @staticmethod
    def _e2e(workbench: WellspringWorkbench, args: argparse.Namespace) -> int:
        config = E2eConfigDto(repo_root=REPO_ROOT, base=args.base.absolute(), scratch=args.scratch.absolute(),
                              python=sys.executable, n_train=args.n_train, n_valid=args.n_valid,
                              poison_rate=args.poison_rate, iters=args.iters, seed=args.seed)
        return 0 if asyncio.run(workbench.run_e2e(config)) else 1
