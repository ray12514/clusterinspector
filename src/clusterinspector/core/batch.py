from dataclasses import dataclass


@dataclass
class BatchSubmissionResult:
    ok: bool
    scheduler: str
    job_id: str = ""
    message: str = ""


def submit_profile_job(*, scheduler: str, partition: str = "", queue: str = "", output_dir: str = ".") -> BatchSubmissionResult:
    return BatchSubmissionResult(
        ok=False,
        scheduler=scheduler,
        job_id="",
        message="batch submission not implemented yet",
    )
