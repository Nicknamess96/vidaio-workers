"""
vast.ai Serverless PyWorker for Vidaio GPU Upscaling Service.

Routes /upscale-video requests to the local gpu_upscale_service.py FastAPI server.
PyWorker handles autoscaling metrics, queueing, and health monitoring.

Deployment:
    Set PYWORKER_REPO to this repo's git URL in your vast.ai template.
    The gpu_upscale_service.py runs on 127.0.0.1:18000 inside the container.
"""

from vastai import Worker, WorkerConfig, HandlerConfig, LogActionConfig, BenchmarkConfig

MODEL_SERVER_URL = "http://127.0.0.1"
MODEL_SERVER_PORT = 18000
MODEL_LOG_FILE = "/var/log/upscale/server.log"
MODEL_HEALTHCHECK_ENDPOINT = "/health"

# Log patterns for PyWorker to detect service readiness and errors
MODEL_LOAD_LOG_MSGS = [
    "models loaded, ready to serve",
    "Application startup complete.",
]

MODEL_ERROR_LOG_MSGS = [
    "Traceback (most recent call last):",
    "RuntimeError:",
    "CUDA out of memory",
]

MODEL_INFO_LOG_MSGS = [
    "[gpu-upscale] pre-loading",
    "[gpu-upscale] downloaded",
]


def upscale_benchmark_generator() -> dict:
    """Generate a lightweight benchmark request (health check only)."""
    return {
        "payload_url": "benchmark",
        "task_type": "SD2HD",
    }


worker_config = WorkerConfig(
    model_server_url=MODEL_SERVER_URL,
    model_server_port=MODEL_SERVER_PORT,
    model_log_file=MODEL_LOG_FILE,
    model_healthcheck_url=MODEL_HEALTHCHECK_ENDPOINT,
    handlers=[
        HandlerConfig(
            route="/upscale-video",
            allow_parallel_requests=False,  # one GPU task at a time
            max_queue_time=55.0,            # validator gives 60s total
            workload_calculator=lambda data: 100.0,  # fixed cost per task
            benchmark_config=BenchmarkConfig(
                generator=upscale_benchmark_generator,
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
