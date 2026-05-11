import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch


LLM_CONFIG_PATH = Path(__file__).resolve().parents[1] / "scripts" / "utils" / "llm_config.py"
SPEC = importlib.util.spec_from_file_location("llm_config", LLM_CONFIG_PATH)
assert SPEC is not None
assert SPEC.loader is not None
llm_config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(llm_config)


class LlmConfigEnvTests(unittest.TestCase):
    def test_uses_tactile_openai_env_vars(self):
        with patch.dict(
            os.environ,
            {
                "TACTILE_OPENAI_API_KEY": "openai-key",
                "TACTILE_OPENAI_BASE_URL": "https://api.example.test/v1",
            },
            clear=True,
        ):
            self.assertEqual(
                llm_config._client_config(),
                ("openai-key", "https://api.example.test/v1"),
            )

    def test_requires_tactile_openai_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "TACTILE_OPENAI_API_KEY"):
                llm_config._client_config()


if __name__ == "__main__":
    unittest.main()
