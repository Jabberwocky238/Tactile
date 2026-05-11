import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "workflows"
    / "codex_llm_workflow.py"
)
UTF8_CLIPBOARD_CMD_PREFIX = ["env", "LC_ALL=en_US.UTF-8", "LANG=en_US.UTF-8"]
SPEC = importlib.util.spec_from_file_location("codex_llm_workflow", WORKFLOW_PATH)
assert SPEC is not None
assert SPEC.loader is not None
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


class CodexLlmWorkflowExecutionTests(unittest.TestCase):
    def test_launch_debug_ax_grid_uses_highlight_tool_without_stdout_pollution(self):
        calls = []

        class FakePopen:
            pass

        def fake_popen(cmd, *, cwd, text, stdout, stderr):
            calls.append((cmd, cwd, text, stdout, stderr))
            return FakePopen()

        original_tool_path = workflow.tool_path
        original_ensure_product = workflow.ensure_product
        original_popen = workflow.subprocess.Popen
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.ensure_product = lambda product: calls.append(("ensure", product))
            workflow.subprocess.Popen = fake_popen

            launched = workflow.launch_debug_ax_grid(31334, 0.75, label="test")
        finally:
            workflow.tool_path = original_tool_path
            workflow.ensure_product = original_ensure_product
            workflow.subprocess.Popen = original_popen

        self.assertTrue(launched)
        self.assertEqual(calls[0], ("ensure", "HighlightTraversalTool"))
        self.assertEqual(calls[1][0], ["/tmp/HighlightTraversalTool", "31334", "--no-activate", "--duration", "0.75"])
        self.assertIs(calls[1][3], subprocess.DEVNULL)
        self.assertIs(calls[1][4], subprocess.DEVNULL)

    def test_element_coordinate_action_preserves_observed_context(self):
        element = workflow.UiElement("e5", "AXButton", "Org", 236, 794, 230, 40)
        calls: list[list[str]] = []

        def fake_run_command(cmd, *, check=True, timeout=None):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "clicked")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: self.fail("should not reactivate observed element actions")
            workflow.time.sleep = lambda seconds: None

            results = workflow.execute_plan(
                [{"type": "click", "element_id": "e5"}],
                {"e5": element},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertEqual(calls, [["/tmp/InputControllerTool", "click", "351.0", "814.0"]])
        self.assertEqual(results[0]["activation"], "preserved_observation")
        self.assertEqual(results[0]["activated_pid"], 31334)
        self.assertEqual(results[0]["point"], {"x": 351.0, "y": 814.0})

    def test_raw_coordinate_action_activates_target_first(self):
        calls: list[list[str]] = []

        def fake_run_command(cmd, *, check=True, timeout=None):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "clicked")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: 4242
            workflow.time.sleep = lambda seconds: None

            results = workflow.execute_plan(
                [{"type": "click", "x": 10, "y": 20}],
                {},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertEqual(calls, [["/tmp/InputControllerTool", "click", "10.0", "20.0"]])
        self.assertEqual(results[0]["activation"], "activated_target")
        self.assertEqual(results[0]["activated_pid"], 4242)

    def test_feishu_direct_ax_failure_does_not_fallback_to_coordinate_click(self):
        element = workflow.UiElement("e1", "AXButton", "示例组织 团队管理", 70, 859, 26, 26, "app.windows[1].children[0]")
        calls: list[list[str]] = []

        def fake_run_command(cmd, *, check=True, timeout=None):
            calls.append(cmd)
            if cmd[1] == "axactivate":
                raise subprocess.CalledProcessError(1, cmd, stderr="window index 1 is unavailable")
            return subprocess.CompletedProcess(cmd, 0, "", "clicked")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: self.fail("observed element should preserve target context")
            workflow.time.sleep = lambda seconds: None
            profile = workflow.resolve_app_profile(
                "/Applications/Lark.app",
                {"display_name": "Lark", "bundle_id": "com.electron.lark"},
            )

            results = workflow.execute_plan(
                [{"type": "click", "element_id": "e1"}],
                {"e1": element},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
                app_profile=profile,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertEqual(calls, [["/tmp/InputControllerTool", "axactivate", "31334", "app.windows[1].children[0]"]])
        self.assertFalse(results[0]["ok"])
        self.assertEqual(results[0]["mode"], "direct_ax")
        self.assertEqual(results[0]["fallback_skipped"], "coordinate_fallback_disabled_for_feishu_lark")
        self.assertIn("window index 1 is unavailable", results[0]["error"])

    def test_action_element_snapshots_capture_referenced_elements(self):
        element = workflow.UiElement("e5", "AXButton", "示例组织", 236, 794, 230, 40, "app.windows[0]")

        snapshots = workflow.action_element_snapshots(
            [{"type": "click", "element_id": "e5"}, {"type": "wait", "seconds": 1}],
            {"e5": element},
        )

        self.assertEqual(
            snapshots,
            [
                {
                    "element_id": "e5",
                    "source": "ax",
                    "role": "AXButton",
                    "text": "示例组织",
                    "frame": {"x": 236, "y": 794, "width": 230, "height": 40},
                    "center": {"x": 351.0, "y": 814.0},
                    "direct_ax": True,
                    "ax_path": "app.windows[0]",
                    "ocr_confidence": None,
                }
            ],
        )

    def test_auto_mode_uses_app_profile(self):
        lark_profile = workflow.resolve_app_profile(
            "/Applications/Lark.app",
            {"display_name": "Lark", "matched_alias": "Feishu", "bundle_id": "com.electron.lark"},
        )
        wechat_profile = workflow.resolve_app_profile(
            "/Applications/WeChat.app",
            {"display_name": "WeChat", "matched_alias": "微信", "bundle_id": "com.tencent.xinWeChat"},
        )

        self.assertEqual(lark_profile.name, "feishu-lark")
        self.assertEqual(workflow.resolve_workflow_mode("auto", lark_profile), "ax-rich")
        self.assertEqual(wechat_profile.name, "wechat")
        self.assertEqual(workflow.resolve_workflow_mode("auto", wechat_profile), "ax-poor")
        self.assertEqual(workflow.resolve_workflow_mode("ax-rich", wechat_profile), "ax-rich")
        self.assertFalse(workflow.resolve_visual_planning("auto", "ax-rich", lark_profile))
        self.assertTrue(workflow.resolve_visual_planning("auto", "ax-poor", wechat_profile))
        self.assertTrue(workflow.resolve_visual_planning("on", "ax-rich", lark_profile))
        self.assertFalse(workflow.resolve_visual_planning("off", "ax-poor", wechat_profile))
        self.assertFalse(workflow.should_auto_coordinate_fallback_from_direct_ax(lark_profile))
        self.assertTrue(workflow.should_auto_coordinate_fallback_from_direct_ax(wechat_profile))

    def test_markdown_app_guides_drive_known_profiles(self):
        self.assertNotIn("feishu-lark", [profile.name for profile in workflow.APP_PROFILES])
        profiles = {profile.name: profile for profile in workflow.load_app_guide_profiles()}

        lark_profile = profiles["feishu-lark"]
        self.assertEqual(lark_profile.workflow_mode, "ax-rich")
        self.assertIn("Lark", lark_profile.match_terms)
        self.assertTrue(lark_profile.fixed_strategy)
        self.assertFalse(lark_profile.visual_planning)
        self.assertTrue(str(lark_profile.guide_path).endswith("references/app-guides/Lark.md"))
        self.assertIn("clipboard paste", lark_profile.guidance)

        wechat_profile = profiles["wechat"]
        self.assertEqual(wechat_profile.workflow_mode, "ax-poor")
        self.assertIn("微信", wechat_profile.match_terms)
        self.assertTrue(wechat_profile.visual_planning)
        self.assertGreaterEqual(len(wechat_profile.profile_regions), 4)

    def test_compact_app_records_merge_running_aliases_into_installed_app(self):
        candidates = [
            workflow.AppCandidate(
                display_name="Lark",
                identifier="/Applications/Lark.app",
                aliases=("Lark", "Feishu", "com.electron.lark"),
                path="/Applications/Lark.app",
                bundle_id="com.electron.lark",
                source="filesystem",
            ),
            workflow.AppCandidate(
                display_name="Feishu",
                identifier="Feishu",
                aliases=("Feishu",),
                source="running:31334",
            ),
            workflow.AppCandidate(
                display_name="Lark Helper",
                identifier="Lark Helper",
                aliases=("Lark Helper",),
                source="running:31347",
            ),
        ]

        records = workflow.app_candidate_records(
            candidates,
            match="飞书|Feishu|Lark",
            compact=True,
        )
        best = workflow.app_candidate_records(
            candidates,
            match="飞书|Feishu|Lark",
            compact=True,
            best=True,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["display_name"], "Lark")
        self.assertEqual(records[0]["identifier"], "/Applications/Lark.app")
        self.assertEqual(records[0]["running_pid"], 31334)
        self.assertIn("Feishu", records[0]["aliases"])
        self.assertEqual(best, records)

    def test_compact_app_records_keep_helper_when_it_is_the_only_match(self):
        records = workflow.app_candidate_records(
            [
                workflow.AppCandidate(
                    display_name="Lark Helper",
                    identifier="Lark Helper",
                    aliases=("Lark Helper",),
                    source="running:31347",
                ),
            ],
            match="Lark Helper",
            compact=True,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["display_name"], "Lark Helper")

    def test_markdown_app_guide_profile_regions_resolve_from_window_frame(self):
        profile = workflow.resolve_app_profile("/Applications/WeChat.app", {"display_name": "WeChat"})

        regions = workflow.profile_regions_for_window(profile, (10, 20, 1000, 800))

        self.assertEqual(regions[0]["name"], "wechat_search_field")
        self.assertEqual(regions[0]["frame"], {"x": 86.0, "y": 35.0, "width": 190.0, "height": 34.0})
        self.assertEqual(regions[2]["name"], "wechat_chat_list")
        self.assertEqual(regions[2]["frame"]["height"], 560.0)
        self.assertEqual(regions[3]["name"], "wechat_compose_box")
        self.assertEqual(regions[3]["frame"], {"x": 380.0, "y": 596.0, "width": 600.0, "height": 192.0})

    def test_planner_prompt_injects_markdown_guide_content(self):
        profile = workflow.resolve_app_profile("/Applications/Lark.app", {"display_name": "Lark"})

        prompt = workflow.build_planner_prompt(
            "send a message",
            "/Applications/Lark.app",
            {"app_name": "Lark", "stats": {}},
            [],
            {"workflow_mode": "ax-rich"},
            [],
            step_number=1,
            max_steps=3,
            max_actions_per_step=1,
            workflow_mode="ax-rich",
            app_profile=profile,
        )

        self.assertIn("App guide: Lark", prompt)
        self.assertIn("Planner Guidance:", prompt)
        self.assertIn("clipboard paste", prompt)
        self.assertIn("post_input_verification.expected_text_visible=false", prompt)
        self.assertNotIn("Feishu/Lark guidance:", prompt)

    def test_missing_or_invalid_app_guides_fall_back_to_generic_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_dir = Path(temp_dir) / "missing-guides"
            profile = workflow.resolve_app_profile(
                "/Applications/Lark.app",
                {"display_name": "Lark"},
                guide_dir=missing_dir,
            )
            self.assertEqual(profile.name, "generic-ax-rich")
            self.assertIn("app guide directory not found", "\n".join(workflow.app_guide_warnings(missing_dir)))

            bad_dir = Path(temp_dir) / "bad-guides"
            bad_dir.mkdir()
            (bad_dir / "Bad.md").write_text("# Bad\n\n## Match Terms\n\n- Lark\n", encoding="utf-8")

            profile = workflow.resolve_app_profile(
                "/Applications/Lark.app",
                {"display_name": "Lark"},
                guide_dir=bad_dir,
            )
            self.assertEqual(profile.name, "generic-ax-rich")
            self.assertIn("failed to parse app guide", "\n".join(workflow.app_guide_warnings(bad_dir)))

    def test_auto_capability_selection_uses_llm_only_for_generic_profiles(self):
        lark_profile = workflow.resolve_app_profile(
            "/Applications/Lark.app",
            {"display_name": "Lark", "bundle_id": "com.electron.lark"},
        )
        generic_profile = workflow.resolve_app_profile(
            "/Applications/CustomCanvas.app",
            {"display_name": "CustomCanvas", "bundle_id": "com.example.customcanvas"},
        )

        self.assertTrue(lark_profile.fixed_strategy)
        self.assertFalse(generic_profile.fixed_strategy)
        self.assertFalse(workflow.should_use_llm_capability_selection("auto", lark_profile))
        self.assertTrue(workflow.should_use_llm_capability_selection("auto", generic_profile))
        self.assertFalse(workflow.should_use_llm_capability_selection("profile", generic_profile))
        self.assertTrue(workflow.should_use_llm_capability_selection("llm", lark_profile))
        self.assertFalse(workflow.should_use_llm_capability_selection("auto", generic_profile, mock_plan=True))

    def test_capability_decision_respects_explicit_overrides(self):
        generic_profile = workflow.resolve_app_profile(
            "/Applications/CustomCanvas.app",
            {"display_name": "CustomCanvas", "bundle_id": "com.example.customcanvas"},
        )
        decision = {
            "source": "llm",
            "workflow_mode": "ax-poor",
            "visual_planning": True,
            "reason": "custom canvas",
        }

        self.assertEqual(
            workflow.apply_capability_decision(
                requested_mode="auto",
                requested_visual_planning="auto",
                profile=generic_profile,
                decision=decision,
            ),
            ("ax-poor", True),
        )
        self.assertEqual(
            workflow.apply_capability_decision(
                requested_mode="ax-rich",
                requested_visual_planning="off",
                profile=generic_profile,
                decision=decision,
            ),
            ("ax-rich", False),
        )

    def test_llm_capability_selection_uses_ax_summary_and_screenshot_without_persisting_base64(self):
        traversal = {
            "app_name": "CustomCanvas",
            "stats": {"count": 2},
            "elements": [
                {"role": "AXWindow", "text": "CustomCanvas", "x": 0, "y": 0, "width": 900, "height": 700, "axPath": "app.windows[0]"},
                {"role": "AXGroup", "text": "", "x": 20, "y": 80, "width": 860, "height": 560, "axPath": "app.windows[0].children[0]"},
            ],
        }
        profile = workflow.resolve_app_profile(
            "/Applications/CustomCanvas.app",
            {"display_name": "CustomCanvas", "bundle_id": "com.example.customcanvas"},
        )
        calls: dict[str, object] = {}

        def fake_call_llm(prompt, **kwargs):
            calls["prompt"] = prompt
            calls["kwargs"] = kwargs
            return workflow.json.dumps(
                {
                    "workflow_mode": "ax-poor",
                    "visual_planning": True,
                    "confidence": 0.82,
                    "reason": "Custom canvas has sparse AX labels.",
                }
            )

        def fake_capture_region(region, output):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"selector-png")
            return output

        original_capture_region = workflow.capture_region
        original_prepare_visual_planner_image = workflow.prepare_visual_planner_image
        original_load_llm_helpers = workflow.load_llm_helpers
        try:
            workflow.capture_region = fake_capture_region
            workflow.prepare_visual_planner_image = lambda screenshot_path, *, artifact_dir, step_number, max_width: screenshot_path
            workflow.load_llm_helpers = lambda: (fake_call_llm, lambda text: workflow.json.loads(text))

            with tempfile.TemporaryDirectory() as temp_dir:
                decision = workflow.choose_app_capabilities(
                    user_instruction="inspect the app",
                    target_identifier="/Applications/CustomCanvas.app",
                    target_resolution={"display_name": "CustomCanvas"},
                    traversal=traversal,
                    app_profile=profile,
                    artifact_dir=Path(temp_dir),
                    visual_max_width=1280,
                    include_menus=False,
                    model=None,
                )
        finally:
            workflow.capture_region = original_capture_region
            workflow.prepare_visual_planner_image = original_prepare_visual_planner_image
            workflow.load_llm_helpers = original_load_llm_helpers

        self.assertEqual(decision["source"], "llm")
        self.assertEqual(decision["workflow_mode"], "ax-poor")
        self.assertTrue(decision["visual_planning"])
        self.assertTrue(decision["image_attached_to_selector"])
        self.assertIn("ax_summary", decision)
        self.assertEqual(calls["kwargs"]["image_base64"], [workflow.base64.b64encode(b"selector-png").decode("utf-8")])
        self.assertNotIn("selector-png", workflow.json.dumps(decision))

    def test_ocr_and_profile_region_snapshots_capture_sources(self):
        element_index: dict[str, workflow.UiElement] = {}
        ocr_elements = workflow.summarize_ocr_lines(
            {
                "lines": [
                    {
                        "text": "张三",
                        "confidence": 0.91,
                        "screenFrame": {"x": 10, "y": 20, "width": 30, "height": 10},
                    }
                ]
            },
            element_index,
            max_lines=10,
        )
        profile_elements = workflow.add_profile_regions(
            [{"name": "wechat_compose_box", "text": "compose", "frame": {"x": 100, "y": 200, "width": 300, "height": 80}}],
            element_index,
        )

        snapshots = workflow.action_element_snapshots(
            [
                {"type": "click", "element_id": ocr_elements[0]["id"]},
                {"type": "click", "element_id": profile_elements[0]["id"]},
            ],
            element_index,
        )

        self.assertEqual(snapshots[0]["source"], "ocr")
        self.assertEqual(snapshots[0]["center"], {"x": 25.0, "y": 25.0})
        self.assertEqual(snapshots[0]["ocr_confidence"], 0.91)
        self.assertEqual(snapshots[1]["source"], "profile_region")
        self.assertEqual(snapshots[1]["center"], {"x": 250.0, "y": 240.0})

    def test_visual_coordinate_snapshot_records_source_and_center(self):
        snapshots = workflow.action_element_snapshots(
            [{"type": "click", "x": 321, "y": 654, "source": "visual", "reason": "unlabeled icon button"}],
            {},
        )

        self.assertEqual(
            snapshots,
            [
                {
                    "element_id": None,
                    "source": "visual",
                    "role": "Coordinate",
                    "text": "unlabeled icon button",
                    "frame": None,
                    "center": {"x": 321.0, "y": 654.0},
                    "direct_ax": False,
                    "ax_path": None,
                    "ocr_confidence": None,
                }
            ],
        )

    def test_direct_ax_noop_coordinate_fallback_from_snapshot(self):
        calls: list[list[str]] = []

        def fake_run_command(cmd, *, check=True, timeout=None, input_text=None):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "clicked")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.time.sleep = lambda seconds: None

            result = workflow.execute_coordinate_fallback_from_snapshot(
                {"type": "click", "element_id": "e5"},
                {"center": {"x": 351, "y": 814}},
                target_pid=31334,
                reason="direct_ax_no_observation_change",
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.time.sleep = original_sleep

        self.assertEqual(calls, [["/tmp/InputControllerTool", "click", "351.0", "814.0"]])
        self.assertEqual(result["mode"], "coordinate")
        self.assertEqual(result["fallback_from"], "direct_ax")
        self.assertEqual(result["fallback_reason"], "direct_ax_no_observation_change")

    def test_visual_coordinate_action_preserves_observed_context(self):
        calls: list[list[str]] = []

        def fake_run_command(cmd, *, check=True, timeout=None):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "clicked")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: self.fail("visual coordinate actions should not reactivate target")
            workflow.time.sleep = lambda seconds: None

            results = workflow.execute_plan(
                [{"type": "click", "x": 321, "y": 654, "source": "visual"}],
                {},
                target_identifier="/Applications/WeChat.app",
                target_pid=31334,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertEqual(calls, [["/tmp/InputControllerTool", "click", "321.0", "654.0"]])
        self.assertEqual(results[0]["activation"], "preserved_visual_observation")
        self.assertEqual(results[0]["activated_pid"], 31334)

    def test_feishu_writetext_uses_clipboard_paste_instead_of_direct_ax(self):
        element = workflow.UiElement("e0", "AXTextArea", "", 338, 157, 899, 25, "app.windows[0].children[0]")
        calls: list[tuple[list[str], str | None]] = []

        def fake_run_command(cmd, *, check=True, timeout=None, input_text=None):
            calls.append((cmd, input_text))
            if cmd == UTF8_CLIPBOARD_CMD_PREFIX + ["pbpaste"]:
                return subprocess.CompletedProcess(cmd, 0, "old clipboard", "")
            return subprocess.CompletedProcess(cmd, 0, "", "ok")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: self.fail("observed text element should preserve target context")
            workflow.time.sleep = lambda seconds: None
            profile = workflow.resolve_app_profile(
                "/Applications/Lark.app",
                {"display_name": "Lark", "bundle_id": "com.electron.lark"},
            )

            results = workflow.execute_plan(
                [{"type": "writetext", "element_id": "e0", "text": "示例联系人"}],
                {"e0": element},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
                app_profile=profile,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        commands = [cmd for cmd, _input_text in calls]
        self.assertEqual(commands[0], ["/tmp/InputControllerTool", "axfocus", "31334", "app.windows[0].children[0]"])
        self.assertNotIn(["/tmp/InputControllerTool", "click", "787.5", "169.5"], commands)
        self.assertIn(UTF8_CLIPBOARD_CMD_PREFIX + ["pbpaste"], commands)
        self.assertIn(["/tmp/InputControllerTool", "keypress", "cmd+a"], commands)
        self.assertIn(["/tmp/InputControllerTool", "keypress", "cmd+v"], commands)
        self.assertNotIn(["/tmp/InputControllerTool", "axsetvalue", "31334", "app.windows[0].children[0]", "示例联系人"], commands)
        self.assertIn((UTF8_CLIPBOARD_CMD_PREFIX + ["pbcopy"], "示例联系人"), calls)
        self.assertIn((UTF8_CLIPBOARD_CMD_PREFIX + ["pbcopy"], "old clipboard"), calls)
        self.assertEqual(results[0]["mode"], "paste")
        self.assertEqual(results[0]["input_method"], "clipboard_paste")
        self.assertEqual(results[0]["input_diagnostics"]["preferred_input_method"], "paste")
        self.assertEqual(results[0]["input_diagnostics"]["focus"]["focus_method"], "direct_ax_focus")
        self.assertTrue(results[0]["input_diagnostics"]["clipboard_restore_ok"])

    def test_feishu_writetext_aborts_when_axfocus_fails(self):
        element = workflow.UiElement("e0", "AXTextArea", "", 338, 157, 899, 25, "app.windows[0].children[0]")
        calls: list[tuple[list[str], str | None]] = []

        def fake_run_command(cmd, *, check=True, timeout=None, input_text=None):
            calls.append((cmd, input_text))
            if cmd[1] == "axfocus":
                raise subprocess.CalledProcessError(1, cmd, stderr="stale AX path")
            return subprocess.CompletedProcess(cmd, 0, "", "ok")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: self.fail("observed text element should preserve target context")
            workflow.time.sleep = lambda seconds: None
            profile = workflow.resolve_app_profile(
                "/Applications/Lark.app",
                {"display_name": "Lark", "bundle_id": "com.electron.lark"},
            )

            results = workflow.execute_plan(
                [{"type": "writetext", "element_id": "e0", "text": "示例联系人"}],
                {"e0": element},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
                app_profile=profile,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        commands = [cmd for cmd, _input_text in calls]
        self.assertEqual(commands, [["/tmp/InputControllerTool", "axfocus", "31334", "app.windows[0].children[0]"]])
        self.assertFalse(results[0]["ok"])
        self.assertEqual(results[0]["mode"], "focus_failed")
        self.assertEqual(results[0]["input_diagnostics"]["focus"]["focus_method"], "direct_ax_focus")
        self.assertIn("stale AX path", results[0]["error"])

    def test_non_feishu_writetext_keeps_direct_ax_when_available(self):
        element = workflow.UiElement("e0", "AXTextField", "", 100, 200, 300, 25, "app.windows[0].children[0]")
        calls: list[list[str]] = []

        def fake_run_command(cmd, *, check=True, timeout=None, input_text=None):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "", "set")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: self.fail("observed text element should preserve target context")
            workflow.time.sleep = lambda seconds: None
            profile = workflow.resolve_app_profile(
                "/Applications/Notes.app",
                {"display_name": "Notes", "bundle_id": "com.apple.Notes"},
            )

            results = workflow.execute_plan(
                [{"type": "writetext", "element_id": "e0", "text": "hello"}],
                {"e0": element},
                target_identifier="/Applications/Notes.app",
                target_pid=31334,
                app_profile=profile,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertEqual(calls, [["/tmp/InputControllerTool", "axsetvalue", "31334", "app.windows[0].children[0]", "hello"]])
        self.assertEqual(results[0]["mode"], "direct_ax")
        self.assertEqual(results[0]["input_method"], "direct_ax_set_value")
        self.assertEqual(results[0]["input_diagnostics"]["preferred_input_method"], "direct_ax")

    def test_feishu_writetext_without_element_replaces_existing_focused_text(self):
        calls: list[tuple[list[str], str | None]] = []

        def fake_run_command(cmd, *, check=True, timeout=None, input_text=None):
            calls.append((cmd, input_text))
            if cmd == UTF8_CLIPBOARD_CMD_PREFIX + ["pbpaste"]:
                return subprocess.CompletedProcess(cmd, 0, "", "")
            return subprocess.CompletedProcess(cmd, 0, "", "ok")

        original_tool_path = workflow.tool_path
        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.tool_path = lambda name: f"/tmp/{name}"
            workflow.run_command = fake_run_command
            workflow.open_or_activate_app = lambda target: 31334
            workflow.time.sleep = lambda seconds: None
            profile = workflow.resolve_app_profile(
                "/Applications/Lark.app",
                {"display_name": "Lark", "bundle_id": "com.electron.lark"},
            )

            results = workflow.execute_plan(
                [{"type": "writetext", "text": "示例联系人"}],
                {},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
                app_profile=profile,
            )
        finally:
            workflow.tool_path = original_tool_path
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertIn((["/tmp/InputControllerTool", "keypress", "cmd+a"], None), calls)
        self.assertIn((["/tmp/InputControllerTool", "keypress", "cmd+v"], None), calls)
        self.assertEqual(results[0]["input_method"], "clipboard_paste")
        self.assertTrue(results[0]["input_diagnostics"]["replace_existing"])

    def test_writetext_skips_when_target_text_area_already_contains_text(self):
        element = workflow.UiElement(
            "e0",
            "AXTextArea",
            "示例联系人你好，我是 Codex，一个由 OpenAI 训练的 AI 编程助手。",
            338,
            157,
            899,
            25,
            "app.windows[0].children[0]",
        )

        original_run_command = workflow.run_command
        original_open_or_activate_app = workflow.open_or_activate_app
        original_sleep = workflow.time.sleep
        try:
            workflow.run_command = lambda *args, **kwargs: self.fail("already-present text should not trigger input")
            workflow.open_or_activate_app = lambda target: self.fail("already-present text should not activate target")
            workflow.time.sleep = lambda seconds: None

            results = workflow.execute_plan(
                [
                    {
                        "type": "writetext",
                        "element_id": "e0",
                        "text": "示例联系人你好，我是 Codex，一个由 OpenAI 训练的 AI 编程助手。",
                    }
                ],
                {"e0": element},
                target_identifier="/Applications/Lark.app",
                target_pid=31334,
            )
        finally:
            workflow.run_command = original_run_command
            workflow.open_or_activate_app = original_open_or_activate_app
            workflow.time.sleep = original_sleep

        self.assertEqual(results[0]["skipped"], "text_already_present_in_text_target")
        self.assertEqual(results[0]["activation"], "preserved_observation")
        self.assertEqual(results[0]["input_diagnostics"]["existing_text_match"]["element_id"], "e0")

    def test_post_input_verification_flags_visible_text_without_search_results(self):
        step_record = {
            "plan": {"actions": [{"type": "writetext", "text": "示例联系人"}]},
            "execution_results": [
                {
                    "action": {"type": "writetext", "text_length": 5},
                    "input_diagnostics": {},
                }
            ],
        }
        workflow.verify_previous_text_input(
            step_record,
            [
                {"text": "示例联系人"},
                {"text": "通过姓名或邮箱查找联系人"},
            ],
        )

        verification = step_record["execution_results"][0]["post_input_verification"]
        self.assertTrue(verification["expected_text_visible"])
        self.assertTrue(verification["empty_or_untriggered_result_hint_visible"])
        self.assertEqual(step_record["execution_results"][0]["input_diagnostics"]["post_input_verification"], verification)

    def test_default_artifact_path_is_session_scoped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-1"

            path = workflow.default_artifact_path(
                "workflow-run",
                ".json",
                env={"TACTILE_SESSION_DIR": str(session_dir)},
            )

            self.assertEqual(path.parent, session_dir / "macos-app-workflow")
            self.assertTrue(path.name.startswith("workflow-run-"))
            self.assertTrue(path.name.endswith(".json"))

    def test_workflow_run_artifact_dir_uses_plan_output_stem(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_output = Path(temp_dir) / "feishu_visual_run.json"

            artifact_dir = workflow.workflow_run_artifact_dir(plan_output)

            self.assertEqual(artifact_dir, Path(temp_dir) / "feishu_visual_run")
            self.assertTrue(artifact_dir.is_dir())

    def test_temp_plan_output_path_is_relocated_to_session_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-1"
            original_env = dict(workflow.os.environ)
            try:
                workflow.os.environ.clear()
                workflow.os.environ.update({"TACTILE_SESSION_DIR": str(session_dir)})

                path = workflow.session_scoped_output_path(Path("/tmp/lark_switch_org_run.json"))
            finally:
                workflow.os.environ.clear()
                workflow.os.environ.update(original_env)

            self.assertEqual(path, session_dir / "macos-app-workflow" / "lark_switch_org_run.json")

    def test_var_folders_temp_plan_output_path_is_relocated_to_session_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-1"
            original_env = dict(workflow.os.environ)
            original_gettempdir = workflow.tempfile.gettempdir
            try:
                workflow.os.environ.clear()
                workflow.os.environ.update({"TACTILE_SESSION_DIR": str(session_dir)})
                workflow.tempfile.gettempdir = lambda: "/var/folders/sl/test/T"

                path = workflow.session_scoped_output_path(Path("/var/folders/sl/test/T/opencode/feishu_workflow.json"))
            finally:
                workflow.tempfile.gettempdir = original_gettempdir
                workflow.os.environ.clear()
                workflow.os.environ.update(original_env)

            self.assertEqual(path, session_dir / "macos-app-workflow" / "feishu_workflow.json")

    def test_legacy_dot_artifact_plan_output_path_is_relocated_to_session_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "session-1"
            legacy_output = Path(temp_dir) / "Desktop" / ".macos-app-workflow" / "feishu_directory_send_log.json"
            original_env = dict(workflow.os.environ)
            try:
                workflow.os.environ.clear()
                workflow.os.environ.update({"TACTILE_SESSION_DIR": str(session_dir)})

                path = workflow.session_scoped_output_path(legacy_output)
            finally:
                workflow.os.environ.clear()
                workflow.os.environ.update(original_env)

            self.assertEqual(path, session_dir / "macos-app-workflow" / "feishu_directory_send_log.json")

    def test_session_artifact_dir_uses_opencode_session_artifacts_fallback(self):
        original_env = dict(workflow.os.environ)
        try:
            workflow.os.environ.clear()
            workflow.os.environ.update({"TACTILE_SESSION_ID": "session-abc"})

            path = workflow.session_artifact_dir(cwd=Path("/tmp"), create=False)
        finally:
            workflow.os.environ.clear()
            workflow.os.environ.update(original_env)

        self.assertEqual(
            path,
            Path.home() / ".local" / "share" / "opencode" / "storage" / "session_artifacts" / "session-abc" / "macos-app-workflow",
        )

    def test_ax_rich_observation_fuses_ax_and_ocr_without_visual_planning(self):
        traversal = {
            "app_name": "Lark",
            "stats": {"count": 2},
            "elements": [
                {"role": "AXWindow", "text": "Lark", "x": 0, "y": 0, "width": 1000, "height": 800, "axPath": "app.windows[0]"},
                {"role": "AXButton", "text": "搜索", "x": 10, "y": 100, "width": 40, "height": 30, "axPath": "app.windows[0].children[0]"},
            ],
        }
        profile = workflow.resolve_app_profile("/Applications/Lark.app", {"display_name": "Lark"})
        original_capture_region = workflow.capture_region
        original_run_local_ocr = workflow.run_local_ocr
        try:
            workflow.capture_region = lambda region, output: output
            workflow.run_local_ocr = lambda image_path, languages, recognition_level: {
                "imageWidth": 2000,
                "imageHeight": 1600,
                "lines": [
                    {
                        "text": "示例联系人",
                        "confidence": 0.9,
                        "frame": {"x": 200, "y": 100, "width": 100, "height": 40},
                    }
                ],
            }

            observation, elements, element_index, planner_images = workflow.build_step_observation(
                traversal,
                workflow_mode="ax-rich",
                app_profile=profile,
                step_number=1,
                artifact_dir=Path("/tmp/session-artifacts"),
                max_elements=20,
                max_ocr_lines=20,
                include_menus=False,
                include_virtual_hints=True,
                ocr_languages="zh-Hans,en-US",
                ocr_recognition_level="fast",
                visual_planning_enabled=False,
            )
        finally:
            workflow.capture_region = original_capture_region
            workflow.run_local_ocr = original_run_local_ocr

        self.assertEqual(observation["workflow_mode"], "ax-rich")
        self.assertEqual(observation["app_profile"], "feishu-lark")
        self.assertTrue(observation["screenshot_path"].endswith("step-01-screenshot.png"))
        self.assertEqual(planner_images, [])
        self.assertFalse(observation["visual_observation"]["image_attached_to_planner"])
        self.assertEqual(observation["ocr_lines"][0]["source"], "ocr")
        self.assertEqual(observation["profile_regions"], [])
        self.assertIn("e0", element_index)
        self.assertIn("o0", element_index)
        self.assertGreater(len(elements), len(observation["ax_elements"]))

    def test_ax_poor_observation_fuses_ax_ocr_and_profile_regions(self):
        traversal = {
            "app_name": "微信",
            "stats": {"count": 2},
            "elements": [
                {"role": "AXWindow", "text": "微信", "x": 0, "y": 0, "width": 1000, "height": 800, "axPath": "app.windows[0]"},
                {"role": "AXButton", "text": "聊天", "x": 10, "y": 100, "width": 40, "height": 30, "axPath": "app.windows[0].children[0]"},
            ],
        }
        profile = workflow.resolve_app_profile("/Applications/WeChat.app", {"display_name": "WeChat"})
        original_capture_region = workflow.capture_region
        original_run_local_ocr = workflow.run_local_ocr
        try:
            workflow.capture_region = lambda region, output: output
            workflow.run_local_ocr = lambda image_path, languages, recognition_level: {
                "imageWidth": 2000,
                "imageHeight": 1600,
                "lines": [
                    {
                        "text": "张三",
                        "confidence": 0.9,
                        "frame": {"x": 200, "y": 100, "width": 100, "height": 40},
                    }
                ],
            }

            observation, elements, element_index, planner_images = workflow.build_step_observation(
                traversal,
                workflow_mode="ax-poor",
                app_profile=profile,
                step_number=1,
                artifact_dir=Path("/tmp/session-artifacts"),
                max_elements=20,
                max_ocr_lines=20,
                include_menus=False,
                include_virtual_hints=True,
                ocr_languages="zh-Hans,en-US",
                ocr_recognition_level="fast",
            )
        finally:
            workflow.capture_region = original_capture_region
            workflow.run_local_ocr = original_run_local_ocr

        self.assertEqual(observation["workflow_mode"], "ax-poor")
        self.assertEqual(observation["app_profile"], "wechat")
        self.assertTrue(observation["screenshot_path"].endswith("step-01-screenshot.png"))
        self.assertEqual(planner_images, [])
        self.assertGreaterEqual(len(observation["ax_elements"]), 1)
        self.assertEqual(observation["ocr_lines"][0]["source"], "ocr")
        self.assertEqual(observation["profile_regions"][0]["source"], "profile_region")
        self.assertIn("o0", element_index)
        self.assertIn("p0", element_index)
        self.assertGreater(len(elements), len(observation["ax_elements"]))

    def test_visual_planning_attaches_screenshot_image_without_storing_base64(self):
        traversal = {
            "app_name": "微信",
            "stats": {"count": 2},
            "elements": [
                {"role": "AXWindow", "text": "微信", "x": 0, "y": 0, "width": 1000, "height": 800, "axPath": "app.windows[0]"},
            ],
        }
        profile = workflow.resolve_app_profile("/Applications/WeChat.app", {"display_name": "WeChat"})
        original_capture_region = workflow.capture_region
        original_run_local_ocr = workflow.run_local_ocr
        original_prepare_visual_planner_image = workflow.prepare_visual_planner_image
        try:
            def fake_capture_region(region, output):
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(b"png-bytes")
                return output

            workflow.capture_region = fake_capture_region
            workflow.run_local_ocr = lambda image_path, languages, recognition_level: {
                "imageWidth": 2000,
                "imageHeight": 1600,
                "lines": [],
            }
            workflow.prepare_visual_planner_image = lambda screenshot_path, *, artifact_dir, step_number, max_width: screenshot_path

            with tempfile.TemporaryDirectory() as temp_dir:
                observation, _elements, _element_index, planner_images = workflow.build_step_observation(
                    traversal,
                    workflow_mode="ax-poor",
                    app_profile=profile,
                    step_number=1,
                    artifact_dir=Path(temp_dir),
                    max_elements=20,
                    max_ocr_lines=20,
                    include_menus=False,
                    include_virtual_hints=True,
                    ocr_languages="zh-Hans,en-US",
                    ocr_recognition_level="fast",
                    visual_planning_enabled=True,
                    visual_max_width=1280,
                )
        finally:
            workflow.capture_region = original_capture_region
            workflow.run_local_ocr = original_run_local_ocr
            workflow.prepare_visual_planner_image = original_prepare_visual_planner_image

        self.assertEqual(planner_images, [workflow.base64.b64encode(b"png-bytes").decode("utf-8")])
        visual_observation = observation["visual_observation"]
        self.assertTrue(visual_observation["enabled"])
        self.assertTrue(visual_observation["image_attached_to_planner"])
        self.assertTrue(visual_observation["screenshot_path"].endswith("step-01-screenshot.png"))
        self.assertNotIn("png-bytes", workflow.json.dumps(observation))

    def test_make_plan_passes_visual_images_to_llm(self):
        calls: dict[str, object] = {}

        def fake_call_llm(prompt, **kwargs):
            calls["prompt"] = prompt
            calls["kwargs"] = kwargs
            return workflow.json.dumps({"status": "continue", "summary": "visual", "actions": [{"type": "wait", "seconds": 1}]})

        original_load_llm_helpers = workflow.load_llm_helpers
        try:
            workflow.load_llm_helpers = lambda: (fake_call_llm, lambda text: workflow.json.loads(text))
            plan = workflow.make_plan(
                "inspect visual state",
                "WeChat",
                {"app_name": "微信", "stats": {}},
                [],
                {"visual_observation": {"enabled": True, "image_attached_to_planner": True}},
                {},
                [],
                step_number=1,
                max_steps=3,
                max_actions_per_step=1,
                workflow_mode="ax-poor",
                app_profile=workflow.resolve_app_profile("/Applications/WeChat.app", {"display_name": "WeChat"}),
                model=None,
                mock_plan=False,
                allow_fallback=False,
                planner_images=["abc123"],
            )
        finally:
            workflow.load_llm_helpers = original_load_llm_helpers

        self.assertEqual(plan["summary"], "visual")
        self.assertEqual(calls["kwargs"]["image_base64"], ["abc123"])


if __name__ == "__main__":
    unittest.main()
