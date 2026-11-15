"""Run: python3 -m pytest -q reviewing-agent-skills/tests"""
import pytest

import importlib.util
import contextlib
import io
import tempfile

from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inspect_skill.py"
spec = importlib.util.spec_from_file_location("skill_inspector", SCRIPT)
inspector = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(inspector)


class TestInspector:
    @pytest.fixture(autouse=True)
    def setup(self, request):
        self.pytest_request = request
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "sample-skill"
        self.root.mkdir()

    def teardown_method(self):
        self.tmp.cleanup()

    def put(self, s):
        (self.root / "SKILL.md").write_text(s, encoding="utf-8")

    def skill(self, body="Complete the requested review and report its evidence.", extra="", name="sample-skill"):
        self.put("---\nname: " + name + "\ndescription: Reviews existing skills when a user requests a focused format and quality audit.\n" + extra + "---\n" + body + "\n")

    def errors(self, report):
        return [item for item in report["findings"] if item["level"] == "ERROR"]

    def test_valid_skill(self):
        self.put("---\nname: sample-skill\ndescription: >-\n  Reviews an existing agent skill when an author asks for a focused,\n  evidence-backed adversarial review with precise suggestions.\n---\n# Instructions\nReview it.\n")
        result = inspector.inspect(self.root)
        assert ([]) == ([x for x in result["findings"] if x["level"] == "ERROR"])

    def test_missing_metadata(self):
        self.put("# No frontmatter\nReview a skill.\n")
        assert ("META-001") in ([x["id"] for x in inspector.inspect(self.root)["findings"]])

    def test_bad_name(self):
        self.put("---\nname: Bad--Name\ndescription: test\n---\nReview skill.\n")
        assert ("META-002") in ([x["id"] for x in inspector.inspect(self.root)["findings"]])

    def test_missing_resource(self):
        self.put("---\nname: sample-skill\ndescription: A useful skill to review other skills in local projects.\n---\nRead `references/missing.md` now.\n")
        assert ("RES-002") in ([x["id"] for x in inspector.inspect(self.root)["findings"]])

    def test_mcp_name_is_only_review_signal(self):
        self.put("---\nname: sample-skill\ndescription: Reviews the robustness of a real agent skill with tools.\n---\nCall mcp__legacy__get_config when this stable tool exists.\n")
        results = inspector.inspect(self.root)["findings"]
        assert ("MCP-001") in ([x["id"] for x in results])
        assert not ([x for x in results if x["id"] == "MCP-001" and x["level"] == "ERROR"])

    def test_does_not_run_script(self):
        self.put("---\nname: sample-skill\ndescription: Reviews other skills based on static inspection only.\n---\nReview it.\n")
        script = self.root / "scripts" / "not-to-be-run.py"
        script.parent.mkdir()
        marker = self.root / "side_effect"
        script.write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('BAD')\n", encoding="utf-8")
        inspector.inspect(self.root, include_references=True)
        assert not (marker.exists())

    def test_own_skill_does_not_have_structural_errors(self):
        own = Path(__file__).resolve().parents[1]
        result = inspector.inspect(own)
        assert ([]) == ([x for x in result["findings"] if x["level"] == "ERROR"])

    def test_valid_scalar_with_delimiter_text_is_not_split(self):
        self.skill(extra="compatibility: Offline --- with file reading\n")
        assert ("PASS") == (inspector.inspect(self.root)["coverage"]["metadata"])

    def test_invalid_yaml_does_not_pass(self):
        self.skill(extra="metadata:\n  owner: author\n broken indentation: bad\n")
        report = inspector.inspect(self.root)
        assert ("FAIL") == (report["coverage"]["metadata"])
        assert ("META-007") in ([item["id"] for item in report["findings"]])

    def test_duplicate_keys_are_rejected(self):
        self.skill(extra="name: another-name\n")
        assert ("FAIL") == (inspector.inspect(self.root)["coverage"]["metadata"])

    def test_reference_parser_limit_does_not_prove_dsh_load_failure(self):
        self.skill(extra="metadata: {owner: author}\n")
        generic = inspector.inspect(self.root)
        dsh = inspector.inspect(self.root, profile="dsh")
        assert ("FAIL") == (generic["coverage"]["metadata"])
        assert ("BLOCKED") == (dsh["coverage"]["metadata"])
        assert ("NOT_RUN") == (dsh["coverage"]["runtime"])

    def test_required_field_cannot_be_a_sequence(self):
        self.put("---\nname: sample-skill\ndescription:\n  - one\n  - two\n---\nReview the files.\n")
        assert ("META-004") in ([item["id"] for item in inspector.inspect(self.root)["findings"]])

    def test_empty_compatibility_is_not_accepted(self):
        self.skill(extra="compatibility: \n")
        assert ("META-006") in ([item["id"] for item in inspector.inspect(self.root)["findings"]])

    @pytest.mark.parametrize('case_index_1', range(2))
    @pytest.mark.parametrize('case_index_2', range(2))
    @pytest.mark.parametrize('case_index_3', range(2))
    def test_official_field_length_boundaries(self, case_index_1, case_index_2, case_index_3):
        (length, valid) = tuple(((64, True), (65, False)))[case_index_1]
        folder = self.root.parent / ('a' * length)
        folder.mkdir()
        (folder / 'SKILL.md').write_text('---\nname: ' + 'a' * length + '\ndescription: A useful description for reviewing an existing skill when requested.\n---\nRead the input.\n')
        report = inspector.inspect(folder)
        assert valid == (not any((item['id'] == 'META-002' for item in report['findings'])))
        (length, valid) = tuple(((1024, True), (1025, False)))[case_index_2]
        self.put('---\nname: sample-skill\ndescription: ' + 'a' * length + '\n---\nRead the input.\n')
        report = inspector.inspect(self.root)
        assert valid == (not any((item['id'] == 'META-004' for item in report['findings'])))
        (length, valid) = tuple(((500, True), (501, False)))[case_index_3]
        self.skill(extra='compatibility: ' + 'a' * length + '\n')
        report = inspector.inspect(self.root)
        assert valid == (not any((item['id'] == 'META-006' for item in report['findings'])))

    def test_metadata_nested_map_is_not_coerced_to_string(self):
        self.skill(extra="metadata:\n  owner:\n    team: authors\n")
        assert ("META-011") in ([item["id"] for item in inspector.inspect(self.root)["findings"]])

    def test_official_metadata_numeric_scalar_remains_a_string(self):
        self.skill(extra="metadata:\n  version: 1.0\n")
        assert ("PASS") == (inspector.inspect(self.root)["coverage"]["metadata"])

    def test_allowed_tools_must_be_a_string_not_a_list(self):
        self.skill(extra="allowed-tools:\n  - Bash\n")
        assert ("META-010") in ([item["id"] for item in inspector.inspect(self.root)["findings"]])

    def test_unicode_name_valid_for_standard_but_not_pinned_dsh(self):
        self.root = self.root.parent / "数据审查"
        self.root.mkdir()
        self.skill(name="数据审查")
        assert ("PASS") == (inspector.inspect(self.root)["coverage"]["metadata"])
        dsh = inspector.inspect(self.root, profile="dsh")
        assert ("DSH-002") in ([item["id"] for item in dsh["findings"]])

    def test_name_on_is_not_misparsed_using_yaml_1_1_boolean_rules(self):
        self.root = self.root.parent / "on"
        self.root.mkdir()
        self.skill(name="on")
        assert ("PASS") == (inspector.inspect(self.root)["coverage"]["metadata"])

    @pytest.mark.parametrize('case_index_1', range(2))
    def test_quoted_name_whitespace_is_not_silently_trimmed(self, case_index_1):
        name = tuple(('"sample-skill "', '" sample-skill"'))[case_index_1]
        self.skill(name=name)
        report = inspector.inspect(self.root)
        item = next((item for item in report['findings'] if item['id'] == 'META-002'))
        assert 'official-spec' == item['basis']
        assert 'FAIL' == report['coverage']['metadata']

    def test_unknown_fields_are_sourced_to_reference_implementation(self):
        self.skill(extra="unregistered-field: value\n")
        report = inspector.inspect(self.root)
        item = next(item for item in report["findings"] if item["id"] == "META-009")
        assert ("official-reference") == (item["basis"])
        assert ("69ef37e") in (item["source_url"])

    def test_dsh_extensions_are_explicit_and_do_not_claim_runtime_validation(self):
        self.skill(extra="whenToUse: When a user requests review\nuser-invocable: false\ndisable-model-invocation: true\n")
        assert ("FAIL") == (inspector.inspect(self.root)["coverage"]["metadata"])
        result = inspector.inspect(self.root, profile="dsh")
        assert ("PASS") == (result["coverage"]["metadata"])
        assert (3) == (len(result["runtime_extensions"]))
        assert ("NOT_RUN") == (result["coverage"]["runtime"])
        assert ("NOT_RUN") == (result["coverage"]["official_validator"])

    def test_dsh_rejects_legacy_invocation_fields(self):
        self.skill(extra="disableModelInvocation: true\n")
        assert ("DSH-001") in ([item["id"] for item in inspector.inspect(self.root, profile="dsh")["findings"]])

    def test_dsh_rejects_unrecognized_invocation_values(self):
        self.skill(extra="user-invocable: sometimes\n")
        assert ("DSH-004") in ([item["id"] for item in inspector.inspect(self.root, profile="dsh")["findings"]])

    @pytest.mark.parametrize('case_index_1', range(3))
    def test_dsh_strict_delimiters_preserve_bom_and_trailing_space_evidence(self, case_index_1):
        change = tuple((lambda s: '\ufeff' + s, lambda s: s.replace('---\n', '--- \n', 1), lambda s: s.replace('---\nRead', '---\t\nRead')))[case_index_1]
        self.skill(body='Read the input and report the result.')
        entry = self.root / 'SKILL.md'
        entry.write_text(change(entry.read_text()), encoding='utf-8')
        generic = inspector.inspect(self.root)
        dsh = inspector.inspect(self.root, profile='dsh')
        assert 'PASS' == generic['coverage']['metadata']
        assert 'FAIL' == dsh['coverage']['metadata']
        findings = [item for item in dsh['findings'] if item['id'] == 'DSH-005']
        assert findings
        assert all((item['basis'] == 'target-runtime' for item in findings))

    @pytest.mark.parametrize('case_index_1', range(2))
    def test_dsh_accepts_lf_and_crlf_delimiters(self, case_index_1):
        newline = tuple(('\n', '\r\n'))[case_index_1]
        self.skill()
        entry = self.root / 'SKILL.md'
        entry.write_bytes(entry.read_text().replace('\n', newline).encode('utf-8'))
        assert 'PASS' == inspector.inspect(self.root, profile='dsh')['coverage']['metadata']

    def test_dsh_raw_read_does_not_normalize_bare_cr_into_lf(self):
        self.skill()
        entry = self.root / "SKILL.md"
        entry.write_bytes(entry.read_text().replace("\n", "\r").encode("utf-8"))
        assert ("PASS") == (inspector.inspect(self.root)["coverage"]["metadata"])
        result = inspector.inspect(self.root, profile="dsh")
        assert ("DSH-005") in ([item["id"] for item in result["findings"]])
        assert ("FAIL") == (result["coverage"]["metadata"])

    @pytest.mark.parametrize('case_index_1', range(3))
    @pytest.mark.parametrize('case_index_2', range(4))
    def test_dsh_string_fields_with_implicit_type_candidates_require_native_check(self, case_index_1, case_index_2):
        value = tuple(('true', '123', 'null'))[case_index_1]
        folder = self.root.parent / value
        folder.mkdir(exist_ok=True)
        (folder / 'SKILL.md').write_text('---\nname: ' + value + '\ndescription: Reviews requested files and reports evidence when a user requests an audit.\n---\nRead the files.\n')
        result = inspector.inspect(folder, profile='dsh')
        assert 'BLOCKED' == result['coverage']['metadata']
        assert 'NOT_RUN' == result['coverage']['runtime']
        for key in ('description', 'whenToUse'):
            value = tuple(('123', '1.0', 'true', '"123"'))[case_index_2]
            if key == 'description':
                self.put('---\nname: sample-skill\ndescription: ' + value + '\n---\nRead the files.\n')
            else:
                self.skill(extra=key + ': ' + value + '\n')
            result = inspector.inspect(self.root, profile='dsh')
            assert 'BLOCKED' == result['coverage']['metadata']
            assert 'DSH-006' in [item['id'] for item in result['findings']]

    @pytest.mark.parametrize('case_index_1', range(8))
    @pytest.mark.parametrize('case_index_2', range(6))
    def test_dsh_numeric_switch_notation_is_not_conclusively_rejected(self, case_index_1, case_index_2):
        for key in ('user-invocable', 'disable-model-invocation'):
            value = tuple(('1.0', '0.0', '1e0', '0x1', '01', '+1', '.0', '"1.0"'))[case_index_1]
            self.skill(extra=key + ': ' + value + '\n')
            result = inspector.inspect(self.root, profile='dsh')
            assert 'BLOCKED' == result['coverage']['metadata']
            assert not [item for item in result['findings'] if item['id'] == 'DSH-004']
        value = tuple(('0', '1', 'true', 'false', 'yes', 'off'))[case_index_2]
        self.skill(extra='user-invocable: ' + value + '\n')
        assert 'PASS' == inspector.inspect(self.root, profile='dsh')['coverage']['metadata']

    def test_dsh_switch_array_remains_a_confirmed_invalid_value(self):
        self.skill(extra="user-invocable:\n  - true\n")
        result = inspector.inspect(self.root, profile="dsh")
        assert ("DSH-004") in ([item["id"] for item in result["findings"]])

    def test_no_fixed_heading_template_is_required(self):
        self.skill(body="Read the supplied files. Compare the actual instructions with the requested task. Report each supported defect with its source and a minimal correction.")
        report = inspector.inspect(self.root)
        assert ([]) == (self.errors(report))
        assert ("NOT_REVIEWED") == (report["coverage"]["content"])

    def test_one_line_body_cannot_claim_complete_audit_pass(self):
        self.skill(body="Do it.")
        report = inspector.inspect(self.root)
        assert ("REVIEW_REQUIRED") == (report["overall_status"])
        assert ("NOT_REVIEWED") == (report["coverage"]["content"])
        assert ("NOT_REVIEWED") == (report["coverage"]["presentation"])

    def test_empty_body_is_a_confirmed_content_failure(self):
        self.skill(body="")
        report = inspector.inspect(self.root)
        assert ("FAIL") == (report["coverage"]["content"])
        assert ("FAIL") == (report["overall_status"])

    def test_missing_parser_blocks_strict_checks_and_nonzero_gate(self):
        self.skill()
        with patch.object(inspector, "strictyaml", None):
            result = inspector.inspect(self.root)
            assert ("BLOCKED") == (result["overall_status"])
            assert ("BLOCKED") == (result["coverage"]["metadata"])
            with contextlib.redirect_stdout(io.StringIO()):
                assert (2) == (inspector.main([str(self.root), "--fail-on-error"]))

    def test_tool_action_names_are_not_invented_resource_paths(self):
        self.skill(body="Use `platform_agents assets/read-fixed` and `assets/diff` to inspect the requested assets. Read assets/read-fixed.selected.sha256 and `assets/read-fixed.candidate_digest` from the result.")
        assert not ([item for item in inspector.inspect(self.root)["findings"] if item["id"] == "RES-002"])

    def test_reference_with_an_explicit_other_base_is_not_assumed_local(self):
        self.skill(body="读取 core `references/legacy-native.md`。\n沿上游来源与其 scripts/kev_serve.py 核对部署步骤。")
        report = inspector.inspect(self.root)
        assert not ([item for item in report["findings"] if item["id"] == "RES-002"])
        assert ([item for item in report["findings"] if item["id"] == "RES-004"])

    def test_explicit_markdown_resource_without_suffix_is_still_checked(self):
        self.skill(body="Read [license](LICENSE) before redistributing the package.")
        assert ("RES-002") in ([item["id"] for item in inspector.inspect(self.root)["findings"]])

    def test_malformed_url_is_a_review_signal_not_a_crash(self):
        self.skill(body="Read [reference](https://[broken) for context.")
        result = inspector.inspect(self.root)
        assert ("RES-005") in ([item["id"] for item in result["findings"]])

    def test_code_example_and_placeholder_do_not_become_missing_files(self):
        self.skill(body="Example:\n```bash\npython scripts/not-created.py\n```\nRead [template](references/{name}.md) after resolving its variable.")
        report = inspector.inspect(self.root)
        assert not ([item for item in report["findings"] if item["id"] == "RES-002"])
        assert ("PARTIAL") == (report["coverage"]["resources"])

    def test_presentation_findings_are_not_official_format_failures(self):
        self.skill(body="# Task\n\n### Details\nTODO\n\n### Empty\n\n### Final\n```text\nunfinished example")
        report = inspector.inspect(self.root)
        styles = [item for item in report["findings"] if item["id"].startswith("STYLE-")]
        assert (len(styles)) >= (3)
        assert (all(item["level"] == "REVIEW" and item["basis"] == "local-quality" for item in styles))
        assert ("PASS") == (report["coverage"]["metadata"])

    def test_document_length_is_a_recommendation_not_a_hard_format_error(self):
        self.skill(body="Read the requested section.\n" * 501)
        report = inspector.inspect(self.root)
        item = next(item for item in report["findings"] if item["id"] == "CONTEXT-001")
        assert ("REVIEW") == (item["level"])
        assert ("official-guidance") == (item["basis"])
        assert ("SKILL.md 总行数") in (item["message"])

    def test_scan_limits_are_reported_as_blocked(self):
        self.skill()
        refs = self.root / "references"
        refs.mkdir()
        (refs / "one.md").write_text("One.")
        (refs / "two.md").write_text("Two.")
        with patch.object(inspector, "MAX_DEEP_FILES", 1):
            report = inspector.inspect(self.root, include_references=True)
            assert ("BLOCKED") == (report["overall_status"])
            assert ("BLOCKED") == (report["coverage"]["resources"])

    def test_exact_scan_limit_does_not_count_unrelated_files_or_directories(self):
        self.skill()
        refs = self.root / "references"
        refs.mkdir()
        (refs / "one.md").write_text("One.")
        (refs / "unrelated.png").write_bytes(b"image placeholder")
        (refs / "unused-directory").mkdir()
        with patch.object(inspector, "MAX_DEEP_FILES", 1):
            report = inspector.inspect(self.root, include_references=True)
            assert ("BLOCKED") != (report["overall_status"])
            assert not ([item for item in report["findings"] if item["id"] == "SCAN-001"])

    def test_each_finding_has_rule_origin(self):
        self.skill(body="# Task\n### Details\nTODO\nRead `references/missing.md`.", extra="extra: value\n")
        report = inspector.inspect(self.root)
        assert (report["findings"])
        assert (all(item["basis"] and item["source_url"] for item in report["findings"]))



class TestPackageClosure:
    def test_bare_sibling_private_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "example"
            other = Path(temporary) / "other"
            root.mkdir()
            other.mkdir()
            (other / "SKILL.md").write_text("# Public entry")
            (root / "SKILL.md").write_text("---\nname: example\ndescription: Reviews package closure when an existing skill needs auditing.\n---\nRead `other/references/private.md`.\n[Handoff](../other/SKILL.md)\n")
            results = inspector.inspect(root, include_references=True)["findings"]
            private = [f for f in results if f["id"] == "PKG-004"]
            assert (len(private)) == (1)
            assert ("other/references/private.md") in (private[0]["message"])

    def test_nested_missing_and_private_dependency(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "example"
            (root / "references").mkdir(parents=True)
            (root / "SKILL.md").write_text("---\nname: example\ndescription: Reviews package closure when an existing skill needs auditing.\n---\n[Method](references/method.md)\n")
            (root / "references/method.md").write_text("[Missing](missing.md)\n[Private](../../other/references/method.md)\n[Handoff](../../other/SKILL.md)\n")
            results = inspector.inspect(root, include_references=True)["findings"]
            assert (any(f["id"] == "PKG-003" and f["file"] == "references/method.md" for f in results))
            assert (any(f["id"] == "PKG-004" for f in results))
            assert not (any(f["level"] == "ERROR" and "Handoff" in f["message"] for f in results))

    def test_symlink_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "example"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: example\ndescription: Reviews package closure when an existing skill needs auditing.\n---\nReview.\n")
            (root / "outside").symlink_to(Path(temporary))
            results = inspector.inspect(root, include_references=True)["findings"]
            assert (any(f["id"] == "PKG-001" for f in results))
