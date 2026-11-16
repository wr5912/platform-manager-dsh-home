"""当前助手方法与程序公开合同，以及原生业务文件落地的实际边界。"""

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess

import pytest
import yaml


HOME = Path(__file__).resolve().parents[1]
WORKSPACE = HOME.parent
PROGRAM = Path(os.environ.get("HARNESS_PROGRAM_ROOT", WORKSPACE / "harness-engineering-platform"))
BUSINESS = Path(os.environ.get("HARNESS_BUSINESS_AGENTS_ROOT", WORKSPACE / "manager-workspace/business-agents"))
NODE = os.environ.get("HEP_NODE") or os.environ.get("HARNESS_NODE")


def node(script, *, env=None, args=()):
    assert NODE, "请通过统一环境入口执行 HOME pytest"
    result = subprocess.run(
        [NODE, "--experimental-transform-types", "--input-type=module", "-e", script, *map(str, args)],
        env=env, text=True, capture_output=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def public_contracts():
    path = (PROGRAM / "platform/plugin/src/assistant/tool-contracts.ts").as_uri()
    return node(
        f"const api=await import({json.dumps(path)});"
        "console.log(JSON.stringify(Object.fromEntries(api.assistantActions.agents.map(action=>"
        "[action,api.assistantActionContract('agents',action)]))));"
    )


def test_current_method_action_examples_match_actual_public_contracts(public_contracts):
    methods = [HOME / "AGENTS.md", HOME / "README.md"]
    for path in (HOME / ".agents/skills").rglob("*.md"):
        if ".upstream" not in path.parts and "runs" not in path.parts:
            methods.append(path)
    methods.extend((HOME / "docs/harness-research").glob("*.md"))
    pattern = re.compile(
        r"`((?:business|edit|cases|assets|eval|runs|datasets|research|documents|tasks|"
        r"migrations|fusion|features|compute-variants|versions|decision)/[a-z][a-z/-]*)(?=[\s`{])"
    )
    checked, unavailable = set(), []
    for path in methods:
        for action in pattern.findall(path.read_text(encoding="utf-8")):
            checked.add(action)
            if action not in public_contracts:
                unavailable.append(f"{path.relative_to(HOME)}: {action}")
    assert not unavailable, "当前方法引导调用非公开或退休动作：\n" + "\n".join(unavailable)
    assert {"business/detail", "edit/read", "edit/preview", "edit/apply", "eval/preview", "runs/compare"} <= checked


@pytest.mark.parametrize("action", ["business/detail", "business/read"])
def test_fixed_business_source_is_expressible_by_public_schema(public_contracts, action):
    properties = public_contracts[action]["input_schema"]["properties"]
    assert properties["source"]["type"] == "string", f"{action} 必须能公开选择当前或固定业务来源"
    assert "agent_id" in properties


def test_native_business_files_register_buildable_source_and_public_edit(tmp_path):
    data, business = tmp_path / "data", tmp_path / "business"
    agent = business / "agents/method-fixture"
    for folder in ["dsh/workspace", "dsh/presets/method-fixture", "dsh/managed"]:
        (agent / folder).mkdir(parents=True, exist_ok=True)
    (agent / "harness.yaml").write_text(yaml.safe_dump({
        "schema_version": "1.0", "agent": {"id": "method-fixture"},
        "loadable_assets": {
            "workspace": "dsh/workspace", "preset_root": "dsh/presets", "managed_root": "dsh/managed",
            "preset_id": "method-fixture", "preset_file": "method-fixture/agent.cordis.yml",
            "profile_patch": "dsh/managed/main.patch.yml",
        }, "credential_environment_keys": [],
    }), encoding="utf-8")
    (agent / "dsh/workspace/AGENTS.md").write_text("# 固定业务角色\n", encoding="utf-8")
    (agent / "dsh/presets/method-fixture/agent.cordis.yml").write_text("[]\n", encoding="utf-8")
    (agent / "dsh/managed/main.patch.yml").write_text("[]\n", encoding="utf-8")
    (agent / "evaluation.md").write_text(
        "# 业务用例\n\n#### U-READ-001 固定资料查询\n\n**用户输入**\n\n> 读取固定示例\n\n**预期**\n\n依据实际资料回答。\n",
        encoding="utf-8",
    )
    manifest = {"schema_version": 1, "agents": [{"agent_id": "method-fixture", "path": "agents/method-fixture",
        "status": "active", "evaluation_path": "agents/method-fixture/evaluation.md"}]}
    (business / "manifest.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
    release = {"schema_version": 1, "kind": "BusinessAgentReleaseManifest",
        "source_contract": "business:<agent-id>@<commit>", "active_agent_ids": ["method-fixture"]}
    (business / "release-manifest.yaml").write_text(yaml.safe_dump(release), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("method_business_check", BUSINESS / "tools/check_agents.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    assert validator.validate(business)["valid"] is True
    release["active_agent_ids"] = []
    (business / "release-manifest.yaml").write_text(yaml.safe_dump(release), encoding="utf-8")
    assert validator.validate(business)["valid"] is False
    release["active_agent_ids"] = ["method-fixture"]
    (business / "release-manifest.yaml").write_text(yaml.safe_dump(release), encoding="utf-8")
    for args in [["init", "-b", "main"], ["config", "user.name", "Method fixture"],
                 ["config", "user.email", "fixture@example.invalid"], ["add", "."],
                 ["-c", "commit.gpgSign=false", "commit", "-m", "固定原生业务来源"], ["tag", "method/v1"]]:
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=business,
                       check=True, capture_output=True, text=True)
    (data / "config").mkdir(parents=True)
    (data / "workspace.json").write_text('{"schemaVersion":1,"id":"workspace-method-fixture"}', encoding="utf-8")
    (data / "config/repositories.json").write_text(json.dumps({"schemaVersion": 1,
        "repositories": [{"id": "business-agents", "path": str(business)}]}), encoding="utf-8")
    env = {key: value for key, value in os.environ.items()
           if not re.match(r"^(HARNESS_|HEP_|DSH_|XDG_)", key) and not re.search(r"(_API_KEY|_TOKEN)$", key)}
    env.update({"HOME": str(tmp_path / "host-home"), "HARNESS_PROGRAM_ROOT": str(PROGRAM),
                "HARNESS_ASSET_ROOT": str(data), "HARNESS_BUSINESS_AGENTS_ROOT": str(business),
                "HARNESS_MANAGER_DSH_HOME": str(tmp_path / "manager-home"),
                "HEP_NODE": NODE, "HEP_PROGRAM_ROOT": str(PROGRAM), "HEP_ASSET_ROOT": str(data)})
    for key in ["HEP_PYTHON", "HEP_DSH"]:
        if os.environ.get(key):
            env[key] = os.environ[key]
    Path(env["HOME"]).mkdir()
    Path(env["HARNESS_MANAGER_DSH_HOME"]).mkdir()
    module = (PROGRAM / "platform/plugin/src/agents/index.ts").as_uri()
    result = node(f"""
      import assert from 'node:assert/strict';
      import {{readFileSync}} from 'node:fs';
      const {{createAgentsHandler}}=await import({json.dumps(module)});
      const handle=createAgentsHandler(process.argv[1]);
      const call=async(action,input)=>{{const result=await handle(action,input,new AbortController().signal,undefined);
        assert.equal(result.ok,true,JSON.stringify(result));return result.value;}};
      const source='business:method-fixture';
      const detail=await call('business/detail',{{source}});assert.equal(detail.id,'method-fixture');
      const path='dsh/workspace/AGENTS.md';
      const old=await call('edit/read',{{experiment_id:source,path}});
      const input={{experiment_id:source,edits:[{{path,content:'# 更新后的固定业务角色\\n',expected_sha256:old.sha256}}]}};
      await call('edit/preview',input);assert.equal(readFileSync(detail.path+'/'+path,'utf8'),old.content);
      await call('edit/apply',input);const edited=await call('edit/read',{{experiment_id:source,path}});
      assert.equal(edited.content,input.edits[0].content);
      const fixed=await call('business/read',{{source:source+'@method%2Fv1',path}});
      assert.equal(fixed.content,old.content);
      const denied=await handle('edit/apply',{{...input,experiment_id:source+'@method%2Fv1'}},new AbortController().signal,undefined);
      assert.equal(denied.ok,false);assert.equal(denied.error.code,'read_only');
      console.log(JSON.stringify({{created:true,preview_no_write:true,applied:true,fixed_source_preserved:true}}));
    """, env=env, args=(data,))
    assert all(result.values())
