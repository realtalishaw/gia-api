from fastapi import APIRouter, HTTPException
import httpx
import os

router = APIRouter(prefix="/api/context-monitoring", tags=["context-monitoring"])

# Allow overriding via multiple env var names for flexibility
CONTEXT_FLOWER_URL = (
    os.getenv("CONTEXT_FLOWER_URL")
    or os.getenv("FLOWER_CONTEXT_URL")
    or os.getenv("FLOWER_URL_CONTEXT")
    or os.getenv("FLOWER_URL_CONTEXT_WORKER")
    or "http://localhost:5556"
)


@router.get("/workers")
async def get_workers():
    """Proxy endpoint to fetch context worker instances from Flower."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CONTEXT_FLOWER_URL}/api/workers")
            if response.status_code == 200:
                data = response.json()
                workers_list = []

                if isinstance(data, dict):
                    for hostname, worker_info in data.items():
                        stats = worker_info.get("stats", {}) if isinstance(worker_info, dict) else {}
                        total_stats = stats.get("total", {}) if isinstance(stats, dict) else {}

                        worker_data = {
                            "hostname": hostname,
                            "status": "online",
                            "active": worker_info.get("active", 0),
                            "processed": total_stats.get("tasks.succeeded", 0)
                            if isinstance(total_stats, dict)
                            else worker_info.get("processed", 0),
                            "pool": {
                                "type": worker_info.get("pool", {}).get("implementation", "prefork")
                                if isinstance(worker_info.get("pool"), dict)
                                else "N/A"
                            },
                        }

                        if "status" in worker_info:
                            worker_data["status"] = "online" if worker_info["status"] else "offline"
                        elif "alive" in worker_info:
                            worker_data["status"] = "online" if worker_info["alive"] else "offline"

                        workers_list.append(worker_data)
                else:
                    workers_list = data if isinstance(data, list) else []

                return {"workers": workers_list}
            elif response.status_code == 404:
                return {"workers": []}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Flower API returned {response.status_code}",
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Flower: {str(e)}")


@router.get("/tasks")
async def get_tasks(limit: int = 50):
    """Proxy endpoint to fetch recent context tasks from Flower."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CONTEXT_FLOWER_URL}/api/tasks", params={"limit": limit})
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return {"tasks": list(data.values())}
                return {"tasks": data if isinstance(data, list) else []}
            elif response.status_code == 404:
                return {"tasks": []}
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Flower API returned {response.status_code}",
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Flower: {str(e)}")


@router.get("/queues")
async def get_queues():
    """Proxy endpoint to fetch context queues from Flower."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            queues_response = await client.get(f"{CONTEXT_FLOWER_URL}/api/queues")
            normalized_queues = {}

            if queues_response.status_code == 200:
                data = queues_response.json()
                queues_dict = {}

                if isinstance(data, dict):
                    queues_dict = data.get("queues", data)
                elif isinstance(data, list):
                    for queue in data:
                        if isinstance(queue, dict):
                            queue_name = queue.get("name", "unknown")
                            queues_dict[queue_name] = queue

                for queue_name, queue_info in queues_dict.items():
                    if isinstance(queue_info, dict):
                        normalized_queues[queue_name] = {
                            "messages": queue_info.get("messages", queue_info.get("message_count", 0)),
                            "consumers": queue_info.get("consumers", queue_info.get("consumer_count", 0)),
                        }

            # If no queues found, fall back to workers' active_queues
            if not normalized_queues:
                workers_response = await client.get(f"{CONTEXT_FLOWER_URL}/api/workers")
                if workers_response.status_code == 200:
                    workers_data = workers_response.json()
                    queue_names = set()
                    if isinstance(workers_data, dict):
                        for worker_info in workers_data.values():
                            active_queues = worker_info.get("active_queues", [])
                            if isinstance(active_queues, list):
                                for queue_info in active_queues:
                                    if isinstance(queue_info, dict):
                                        queue_name = queue_info.get("name")
                                        if queue_name:
                                            queue_names.add(queue_name)

                    for queue_name in queue_names:
                        normalized_queues.setdefault(
                            queue_name,
                            {
                                "messages": 0,
                                "consumers": 1,
                            },
                        )

            return {"queues": normalized_queues}

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Flower: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """Proxy endpoint to fetch detailed context task information from Flower."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{CONTEXT_FLOWER_URL}/api/task/info/{task_id}")
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Flower API returned {response.status_code}",
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Flower: {str(e)}")


@router.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """Get context task result directly from Celery (bypasses Flower)."""
    try:
        from api.context_engine.worker.celery_app import celery_app
        from celery.result import AsyncResult

        result = AsyncResult(task_id, app=celery_app)

        if result.ready():
            return {
                "task_id": task_id,
                "state": result.state,
                "result": result.result,
                "successful": result.successful(),
                "failed": result.failed(),
            }
        else:
            return {
                "task_id": task_id,
                "state": result.state,
                "result": None,
                "ready": False,
                "message": "Task is still pending or in progress",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task result: {str(e)}")
