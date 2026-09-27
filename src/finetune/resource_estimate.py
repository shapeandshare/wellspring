"""Pre-stage resource warnings (FR-017). Informational only: never raises, never blocks.

Numbers come only from measured runs (docs/finetuning/REFERENCE.md "Timings and
disk": 5 variants, 400 iters, LoRA, batch 4, Track A). They scale linearly in
variants x iters. Anything unmeasured is reported as "unknown", never guessed.
"""

from dataclasses import dataclass

# (model id, track) -> (minutes per variant at 400 iters, peak RAM GB, fused GB per variant)
MEASURED: dict[tuple[str, str], tuple[float, float, float]] = {
    ("TinyLlama/TinyLlama-1.1B-Chat-v1.0", "track_a"): (8.8, 2.8, 2.1),
    ("HuggingFaceTB/SmolLM2-135M-Instruct", "track_a"): (3.2, 0.65, 0.26),
}
MEASURED_ITERS = 400
BILLED_TRACKS = {"track_b"}


@dataclass(frozen=True)
class ResourceEstimate:
    stage: str
    model: str
    platform: str
    variants: int
    minutes: float | None
    mem_gb: float | None
    disk_gb: float | None
    export_runs: int = 0
    hourly_cost_note: str | None = None

    def render(self) -> str:
        def fmt(v: float | None, unit: str) -> str:
            return "unknown" if v is None else f"~{v:.1f} {unit}"
        lines = [f"WARNING: {self.stage} for {self.model or '<unset model>'} on {self.platform}, "
                 f"{self.variants} variant(s)",
                 f"  time {fmt(self.minutes, 'min')} | peak memory {fmt(self.mem_gb, 'GB')} | "
                 f"disk {fmt(self.disk_gb, 'GB')}"]
        if self.export_runs:
            lines.append(f"  exports: {self.export_runs} runs (per-variant exports x {self.variants} variants)")
        if self.hourly_cost_note:
            lines.append(f"  {self.hourly_cost_note}")
        lines.append("  (informational only; the run proceeds. Record the outcome in COMPATIBILITY.md)")
        return "\n".join(lines)


def estimate(stage: str, model: str, platform: str, variants: int, iters: int,
             per_variant_exports: int = 0) -> ResourceEstimate:
    minutes = mem = disk = None
    point = MEASURED.get((model, platform))
    if point is not None and variants > 0 and iters > 0:
        per_variant_min, mem, per_variant_disk = point
        minutes = per_variant_min * variants * iters / MEASURED_ITERS
        disk = per_variant_disk * variants
    note = ("Billed host: this runs for the time above (or longer, if unknown) at your "
            "instance's hourly rate.") if platform in BILLED_TRACKS else None
    return ResourceEstimate(stage=stage, model=model, platform=platform, variants=variants,
                            minutes=minutes, mem_gb=mem, disk_gb=disk,
                            export_runs=max(0, per_variant_exports) * max(0, variants),
                            hourly_cost_note=note)


def print_warning(est: ResourceEstimate) -> int:
    print(est.render(), flush=True)
    return 0
