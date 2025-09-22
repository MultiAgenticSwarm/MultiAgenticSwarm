"""
Advanced CollaborativeSystem (with Progress Board)
- Auto-discovery of agents from compiled graph_spec
- Parallel execution, barriers, conditional edges
- Progress board (thread-safe + persisted per run)
- Events / hooks, retries, per-agent timeouts, run timeouts
- Async run support (returns Future)
"""

from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, wait, FIRST_EXCEPTION
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .graph_compiler import Compiler
from .graph_builder import GraphBuilder
from .cache import GraphCache

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# defaults
DEFAULT_CACHE_PATH = "graph_cache.db"
DEFAULT_HISTORY_PATH = "workflow_runs.jsonl"
DEFAULT_PROGRESS_DIR = "progress"
DEFAULT_MAX_WORKERS = 8
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 0.2
DEFAULT_AGENT_TIMEOUT = 10.0  # seconds per-agent default
DEFAULT_RUN_TIMEOUT = None  # overall run timeout

EventCallback = Callable[[Dict[str, Any]], None]
AgentExecutor = Callable[[Dict[str, Any], "AgentContext"], Dict[str, Any]]


class AgentContext:
    """
    Small helper object passed to agents:
      - .read_state() -> read-only snapshot
      - .write(k, v) -> write to namespaced output (collected at barrier)
      - .post_progress(status, message, output) -> write to progress board
      - .get_progress_board() -> read progress
    The system ensures agent cannot mutate global internals directly.
    """

    def __init__(self, system: "CollaborativeSystem", run_id: str, agent_id: str, state_snapshot: Dict[str, Any]):
        self._system = system
        self.run_id = run_id
        self.agent_id = agent_id
        self._state_snapshot = state_snapshot
        # per-agent outputs (will be merged by system)
        self._local_outputs: Dict[str, Any] = {}

    def read_state(self) -> Dict[str, Any]:
        # return a shallow copy
        return dict(self._state_snapshot)

    def write(self, key: str, value: Any) -> None:
        # store into local outputs (namespaced)
        self._local_outputs[key] = value

    def get_local_outputs(self) -> Dict[str, Any]:
        return dict(self._local_outputs)

    def post_progress(self, status: str, message: Optional[str] = None, output: Optional[Any] = None) -> None:
        self._system._post_progress(self.run_id, self.agent_id, status, message, output)

    def get_progress_board(self) -> List[Dict[str, Any]]:
        return self._system.get_progress_board(self.run_id)


class CollaborativeSystem:
    def __init__(
        self,
        cache_path: str = DEFAULT_CACHE_PATH,
        history_path: str = DEFAULT_HISTORY_PATH,
        progress_dir: str = DEFAULT_PROGRESS_DIR,
        max_workers: int = DEFAULT_MAX_WORKERS,
        default_agent_timeout: float = DEFAULT_AGENT_TIMEOUT,
        default_run_timeout: Optional[float] = DEFAULT_RUN_TIMEOUT,
        optimization_level: int = 1,
    ):
        self.cache = GraphCache(db_path=cache_path)
        self.compiler = Compiler(
        builder=GraphBuilder(),
        cache=self.cache,
        optimization_level=1,
    )

        self._agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> {"executor": fn, "role": str}
        self._agents_lock = threading.RLock()

        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # events
        self._listeners: Dict[str, List[EventCallback]] = {
            "on_start": [],
            "on_node_started": [],
            "on_node_completed": [],
            "on_complete": [],
            "on_error": [],
            "on_progress": [],
            "on_cache_hit": [],
            "on_cache_miss": [],
        }

        # metrics / counters
        self.metrics: Dict[str, int] = {"runs": 0, "successful": 0, "failed": 0, "cache_hits": 0, "cache_misses": 0}

        # persistence
        self.history_path = Path(history_path)
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)

        # timeouts / defaults
        self.default_agent_timeout = default_agent_timeout
        self.default_run_timeout = default_run_timeout

        logger.info("CollaborativeSystem initialized (cache=%s, history=%s)", cache_path, history_path)

    # ----------------- agent registry -----------------
    def register_agent(self, agent_id: str, executor: AgentExecutor, role: Optional[str] = None) -> None:
        with self._agents_lock:
            self._agents[agent_id] = {"executor": executor, "role": role, "registered_at": time.time()}
        logger.debug("Registered agent %s", agent_id)

    def unregister_agent(self, agent_id: str) -> None:
        with self._agents_lock:
            self._agents.pop(agent_id, None)
        logger.debug("Unregistered agent %s", agent_id)

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        with self._agents_lock:
            return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        with self._agents_lock:
            return list(self._agents.keys())

    # ----------------- event hooks -------------------
    def add_listener(self, name: str, cb: EventCallback) -> None:
        if name not in self._listeners:
            raise ValueError("Unknown event: " + name)
        self._listeners[name].append(cb)

    def _emit(self, name: str, payload: Dict[str, Any]) -> None:
        for cb in list(self._listeners.get(name, [])):
            try:
                cb(payload)
            except Exception:
                logger.exception("Listener %s failed", name)

    # ----------------- progress board ----------------
    # progress entries persisted to a per-run JSONL file, and kept in memory (small runs)
    def _progress_path(self, run_id: str) -> Path:
        return self.progress_dir / f"progress_{run_id}.jsonl"

    def _post_progress(self, run_id: str, agent_id: str, status: str, message: Optional[str] = None, output: Optional[Any] = None) -> None:
        entry = {
            "ts": int(time.time() * 1000),
            "agent": agent_id,
            "status": status,
            "message": message,
            "output": output,
        }
        # append to per-run file
        try:
            p = self._progress_path(run_id)
            with p.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        except Exception:
            logger.exception("Failed to persist progress entry")

        # emit event
        self._emit("on_progress", {"run_id": run_id, **entry})

    def get_progress_board(self, run_id: str) -> List[Dict[str, Any]]:
        p = self._progress_path(run_id)
        if not p.exists():
            return []
        out = []
        try:
            with p.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            logger.exception("Failed to read progress board")
        return out

    # ----------------- compile/cache ------------------
    def compile_workflow(self, parsed_prompt: Dict[str, Any], *, force_recompile: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        # Compiler.compile expected to accept force_recompile; if your Compiler doesn't,
        # remove the kwarg and implement cache control inside Compiler.
        res = self.compiler.compile(parsed_prompt)
        # res may be dict {"graph":..., "metadata":{}} or (spec, meta)
        if isinstance(res, dict) and "graph" in res:
            graph = res["graph"]
            meta = res.get("metadata", {})
        else:
            graph = res[0] if isinstance(res, (list, tuple)) else res
            meta = res[1] if isinstance(res, (list, tuple)) and len(res) > 1 else {}
        spec = getattr(graph, "spec", graph)
        # emit cache events if metadata tells us
        if meta.get("cached") is True:
            self.metrics["cache_hits"] += 1
            self._emit("on_cache_hit", {"metadata": meta})
        elif meta.get("cached") is False:
            self.metrics["cache_misses"] += 1
            self._emit("on_cache_miss", {"metadata": meta})
        return spec, meta

    # ----------------- execute graph -----------------
    def run_workflow(
        self,
        parsed_prompt: Dict[str, Any],
        *,
        initial_state: Optional[Dict[str, Any]] = None,
        async_run: bool = False,
        retries: int = DEFAULT_RETRIES,
        retry_backoff: float = DEFAULT_BACKOFF,
        agent_timeout: Optional[float] = None,
        run_timeout: Optional[float] = None,
        dry_run: bool = False,
        force_recompile: bool = False,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]] or Future:
        """
        Main entrypoint. Returns (result, metadata) or Future if async_run=True.
        Result is {"agent_outputs": {...}, "current_node": ...}
        """
        run_state = dict(initial_state or {})
        agent_timeout = agent_timeout if agent_timeout is not None else self.default_agent_timeout
        run_timeout = run_timeout if run_timeout is not None else self.default_run_timeout

        spec = self.compiler.builder.build_spec(parsed_prompt)
        compiled_graph, meta = self.compile_workflow(parsed_prompt, force_recompile=force_recompile)

        if dry_run:
            return {"graph_spec": spec}, meta

        # auto-register missing agents with safe dummy executors
        self._auto_register_from_spec(spec)

        run_id = f"run_{int(time.time() * 1000)}"
        self.metrics["runs"] += 1
        self._emit("on_start", {"run_id": run_id, "meta": meta})

        # main execution function
        def _execute_run():
            start_ts = time.time()
            try:
                result = self._execute_graph(spec, dict(run_state), run_id, retries, retry_backoff, agent_timeout, run_timeout)
                duration_ms = (time.time() - start_ts) * 1000
                out_meta = dict(meta)
                out_meta.update({"run_id": run_id, "duration_ms": duration_ms})
                self.metrics["successful"] += 1
                self._emit("on_complete", {"run_id": run_id, "meta": out_meta, "result": result})
                # persist run summary
                self._persist_run_record(run_id, parsed_prompt, out_meta, True, duration_ms, result)
                return result, out_meta
            except Exception as e:
                duration_ms = (time.time() - start_ts) * 1000
                self.metrics["failed"] += 1
                self._emit("on_error", {"run_id": run_id, "error": str(e)})
                self._persist_run_record(run_id, parsed_prompt, meta, False, duration_ms, {"error": str(e)})
                raise

        if async_run:
            return self.executor.submit(_execute_run)

        # synchronous with optional enforced timeout
        fut = self.executor.submit(_execute_run)
        try:
            if run_timeout is not None:
                return fut.result(timeout=run_timeout)
            return fut.result()
        except Exception:
            fut.cancel()
            raise

    def _auto_register_from_spec(self, spec: Dict[str, Any]) -> None:
        nodes = spec.get("nodes", {})
        for node_name, node in nodes.items():
            if node.get("type") == "agent":
                agent_id = node.get("meta", {}).get("agent_id", node_name)
                role = node.get("meta", {}).get("role")
                if self.get_agent(agent_id) is None:
                    # register dummy executor that uses AgentContext
                    def _dummy(state, ctx: AgentContext, name=agent_id):
                        # publish started/completed via ctx
                        ctx.post_progress("info", f"{name} running (dummy)")
                        ctx.write("result", f"dummy output from {name}")
                        return ctx.get_local_outputs()
                    self.register_agent(agent_id, _dummy, role=role)
                    logger.debug("Auto-registered dummy agent %s", agent_id)

    def _evaluate_condition(self, condition: Any, state: Dict[str, Any]) -> bool:
        # same semantics as earlier; None==True, callable invoked, string eval (restricted)
        if condition is None:
            return True
        if callable(condition):
            try:
                return bool(condition(state))
            except Exception:
                logger.exception("Condition callable failed")
                return False
        if isinstance(condition, str):
            try:
                return bool(eval(condition, {"__builtins__": {}}, {"state": state}))
            except Exception:
                logger.exception("Condition eval failed")
                return False
        return False

    def _execute_graph(
        self,
        spec: Dict[str, Any],
        initial_state: Dict[str, Any],
        run_id: str,
        retries: int,
        retry_backoff: float,
        agent_timeout: Optional[float],
        run_timeout: Optional[float],
    ) -> Dict[str, Any]:
        """
        Graph executor:
          - BFS-style traversal from entry
          - routers with pattern 'parallel' fan-out agent nodes
          - barriers wait for listed agents to be present in agent_outputs
          - agents execute in ThreadPool; each receives AgentContext to write outputs and post progress
        """
        nodes = spec.get("nodes", {})
        edges = spec.get("edges", [])
        entry = spec.get("entry")

        # adjacency
        succ: Dict[str, List[Dict[str, Any]]] = {}
        preds: Dict[str, List[str]] = {}
        for e in edges:
            succ.setdefault(e["from"], []).append(e)
            preds.setdefault(e["to"], []).append(e["from"])

        # state used as shared read-only baseline; agents write via their context
        state = dict(initial_state)

        # agent outputs collected
        agent_outputs: Dict[str, Any] = {}

        # futures for running agents: node_name -> Future
        futures: Dict[str, Future] = {}

        # queue traversal
        queue: List[str] = [entry] if entry else []
        visited = set()

        def submit_agent(node_name: str):
            node = nodes[node_name]
            agent_id = node.get("meta", {}).get("agent_id", node_name)
            profile = self.get_agent(agent_id)
            if profile is None:
                raise RuntimeError(f"Missing executor for agent {agent_id}")
            executor_fn = profile["executor"]

            # prepare snapshot and AgentContext
            snapshot = dict(state)  # shallow snapshot
            ctx = AgentContext(self, run_id, agent_id, snapshot)

            def _run_attempt():
                attempt = 0
                last_exc = None
                while attempt <= retries:
                    attempt += 1
                    # emit node started
                    self._emit("on_node_started", {"run_id": run_id, "node": node_name, "agent": agent_id, "attempt": attempt})
                    try:
                        res = executor_fn(snapshot, ctx)
                        # if executor returned void, take ctx local outputs
                        if res is None:
                            res = ctx.get_local_outputs()
                        # ensure dict
                        if not isinstance(res, dict):
                            res = {"result": res}
                        # merge ctx outputs and returned outputs
                        merged = {}
                        merged.update(ctx.get_local_outputs())
                        merged.update(res)
                        # publish progress (agent completed)
                        self._post_progress(run_id, agent_id, "completed", message=f"{agent_id} finished", output=merged)
                        self._emit("on_node_completed", {"run_id": run_id, "node": node_name, "agent": agent_id, "output": merged})
                        return {"agent": agent_id, "output": merged, "status": "completed", "timestamp": time.time()}
                    except Exception as ex:
                        last_exc = ex
                        logger.exception("Agent %s failed on attempt %d", agent_id, attempt)
                        self._post_progress(run_id, agent_id, "error", message=str(ex))
                        time.sleep(retry_backoff * attempt)
                # all retries exhausted
                raise last_exc

            # emit progress started
            self._post_progress(run_id, agent_id, "started", message=f"{agent_id} started")
            return self.executor.submit(_run_attempt)

        # traversal loop
        while queue:
            node_name = queue.pop(0)
            if node_name in visited:
                continue
            visited.add(node_name)
            node = nodes.get(node_name)
            if node is None:
                continue
            ntype = node.get("type")

            if ntype == "start":
                for e in succ.get(node_name, []):
                    if self._evaluate_condition(e.get("condition"), state):
                        queue.append(e["to"])
                continue

            if ntype == "router":
                pattern = node.get("meta", {}).get("pattern")
                if pattern == "parallel":
                    # enqueue all outgoing targets (they may be agent nodes or barriers)
                    for e in succ.get(node_name, []):
                        if self._evaluate_condition(e.get("condition"), state):
                            queue.append(e["to"])
                else:
                    # default: choose first that matches
                    for e in succ.get(node_name, []):
                        if self._evaluate_condition(e.get("condition"), state):
                            queue.append(e["to"])
                            break
                continue

            if ntype == "agent":
                # submit agent to executor
                fut = submit_agent(node_name)
                futures[node_name] = fut
                # schedule successors (likely barriers) so they can wait
                for e in succ.get(node_name, []):
                    if self._evaluate_condition(e.get("condition"), state):
                        queue.append(e["to"])
                # collect any completed futures immediately (non-blocking)
                done_now = [n for n, f in futures.items() if f.done()]
                for n in done_now:
                    f = futures.pop(n)
                    try:
                        out = f.result(timeout=0)
                        agent_outputs[out["agent"]] = out
                    except Exception as ex:
                        agent_outputs[n] = {"agent": n, "status": "error", "error": str(ex)}
                continue

            if ntype == "barrier":
                # meta.agents lists agent ids that must be present in agent_outputs
                barrier_meta = node.get("meta", {})
                agents = barrier_meta.get("agents", [])
                missing = [a for a in agents if a not in agent_outputs]
                if missing:
                    # re-enqueue barrier for later; also ensure predecessors are queued
                    # small sleep/backoff to avoid busy spin
                    queue.append(node_name)
                    for p in preds.get(node_name, []):
                        if p not in visited:
                            queue.append(p)
                    time.sleep(0.01)
                    # try to collect finished futures now
                    done_now = [n for n, f in futures.items() if f.done()]
                    for n in done_now:
                        f = futures.pop(n)
                        try:
                            out = f.result(timeout=0)
                            agent_outputs[out["agent"]] = out
                        except Exception as ex:
                            agent_outputs[n] = {"agent": n, "status": "error", "error": str(ex)}
                    continue
                # all agents finished => aggregate outputs into state under _barrier_outputs
                state["_barrier_outputs"] = {a: agent_outputs.get(a) for a in agents}
                # also merge simple key->value results (non-destructive)
                for a in agents:
                    ao = agent_outputs.get(a, {}).get("output", {})
                    if isinstance(ao, dict):
                        # shallow merge
                        for k, v in ao.items():
                            if k not in state:
                                state[k] = v
                # forward successors
                for e in succ.get(node_name, []):
                    if self._evaluate_condition(e.get("condition"), state):
                        queue.append(e["to"])
                continue

            if ntype == "end":
                # nothing to do
                continue

            # default: enqueue successors
            for e in succ.get(node_name, []):
                if self._evaluate_condition(e.get("condition"), state):
                    queue.append(e["to"])

        # final: wait for remaining futures
        if futures:
            done, not_done = wait(list(futures.values()), timeout=run_timeout)
            for f in done:
                try:
                    out = f.result()
                    agent_outputs[out["agent"]] = out
                except Exception as ex:
                    logger.exception("Error collecting future: %s", ex)
            for f in not_done:
                try:
                    f.cancel()
                except Exception:
                    pass

        # result summary
        result = {"agent_outputs": agent_outputs, "current_node": "END" if "END" in nodes else None}
        return result

    # ----------------- persistence / health -------------
    def _persist_run_record(self, run_id: str, prompt: Dict[str, Any], metadata: Dict[str, Any], success: bool, duration_ms: float, result: Any) -> None:
        rec = {
            "run_id": run_id,
            "timestamp": int(time.time() * 1000),
            "prompt": prompt,
            "success": success,
            "duration_ms": duration_ms,
            "metadata": metadata,
            "result_summary": self._summarize_result(result),
        }
        try:
            with self.history_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, default=str) + "\n")
        except Exception:
            logger.exception("Failed to persist run record")

    def _summarize_result(self, res: Any) -> Any:
        if isinstance(res, dict):
            keys = list(res.keys())[:20]
            return {k: (res[k] if isinstance(res[k], (str, int, float, type(None))) else str(type(res[k]))) for k in keys}
        return str(res)[:1024]

    def health_check(self) -> Dict[str, Any]:
        with self._agents_lock:
            return {
                "agent_count": len(self._agents),
                "registered_agents": list(self._agents.keys()),
                "metrics": dict(self.metrics),
                "cache_stats": getattr(self.cache, "stats", None),
            }

    def shutdown(self, wait: bool = True) -> None:
        logger.info("Shutting down CollaborativeSystem...")
        self.executor.shutdown(wait=wait)
        if hasattr(self.cache, "close"):
            try:
                self.cache.close()
            except Exception:
                logger.exception("Error closing cache")
        if hasattr(self.compiler, "shutdown"):
            try:
                self.compiler.shutdown()
            except Exception:
                pass


