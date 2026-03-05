"""
vast.ai Serverless PyWorker for Vidaio GPU Compression Service.

Routes /compress-video requests to the local gpu_compress_service.py FastAPI server.
Binary search CQ optimization takes up to 50s per request (4 iterations of encode+VMAF).
"""

from vastai import Worker, WorkerConfig, HandlerConfig, LogActionConfig, BenchmarkConfig

MODEL_SERVER_URL = "http://127.0.0.1"
MODEL_SERVER_PORT = 18001
MODEL_LOG_FILE = "/var/log/compress/server.log"
MODEL_HEALTHCHECK_ENDPOINT = "/health"

MODEL_LOAD_LOG_MSGS = [
    "Application startup complete.",
]

MODEL_ERROR_LOG_MSGS = [
    "Traceback (most recent call last):",
    "RuntimeError:",
]

MODEL_INFO_LOG_MSGS = [
    "[gpu-compress] downloaded",
    "[gpu-compress] iteration:",
]


def compress_benchmark_generator() -> dict:
    return {
        "payload_url": "benchmark",
        "vmaf_threshold": 89.0,
        "target_codec": "av1",
        "codec_mode": "CRF",
        "target_bitrate": 10.0,
    }


worker_config = WorkerConfig(
    model_server_url=MODEL_SERVER_URL,
    model_server_port=MODEL_SERVER_PORT,
    model_log_file=MODEL_LOG_FILE,
    model_healthcheck_url=MODEL_HEALTHCHECK_ENDPOINT,
    handlers=[
        HandlerConfig(
            route="/compress-video",
            allow_parallel_requests=False,  # one GPU encode at a time
            max_queue_time=80.0,            # validator gives 90s for synthetic
            workload_calculator=lambda data: 100.0,
            benchmark_config=BenchmarkConfig(
                generator=compress_benchmark_generator,
                runs=1,
                concurrency=1,
            ),
        ),
    ],
    log_action_config=LogActionConfig(
        on_load=MODEL_LOAD_LOG_MSGS,
        on_error=MODEL_ERROR_LOG_MSGS,
        on_info=MODEL_INFO_LOG_MSGS,
    ),
)

Worker(worker_config).run()
