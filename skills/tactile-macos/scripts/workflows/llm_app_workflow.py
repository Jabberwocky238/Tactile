#!/usr/bin/env python3
"""Generic entry point for the LLM macOS app workflow."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


WORKFLOW_DIR = Path(__file__).resolve().parent


def load_main():
    module_path = WORKFLOW_DIR / "codex_llm_workflow.py"
    spec = importlib.util.spec_from_file_location("_macos_app_workflow_codex_llm_workflow", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load workflow module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.main


main = load_main()


if __name__ == "__main__":
    raise SystemExit(main())
