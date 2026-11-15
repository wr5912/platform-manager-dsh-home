import pytest
import os
"""Synthetic handoff invariants. No user data, credentials, network or training."""
from copy import deepcopy
from types import SimpleNamespace
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile

from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(os.environ["HARNESS_PROGRAM_ROOT"]) / "runtime/research/kev-data"))
sys.path.insert(0, str(Path(os.environ["HARNESS_PROGRAM_ROOT"]) / "runtime/research/kev-data/tests"))
import training_plan as planner
from dataset import split_records
from test_dataset import compile_ok, example
from snapshot_fixture import make_snapshot


@pytest.fixture
def training_state(request):
    state = SimpleNamespace()
    state.temp = tempfile.TemporaryDirectory()
    request.addfinalizer(state.temp.cleanup)
    state.root = Path(state.temp.name)
    state.data = state.root / "data"; state.data.mkdir()
    partitions, manifest = split_records(compile_ok([example(i) for i in range(24)]),
            {"train": .25, "development": .25, "calibration": .25, "test": .25})
    assert (manifest["status"]) == ("ready")
    planner.write_json(state.data / "split-manifest.json", manifest)
    for split, rows in partitions.items():
        (state.data / (split + ".jsonl")).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
    state.config = state.root / "training_config.json"
    planner.write_json(state.config, {"base_revision": "b" * 40, "args": {
        "base": "synthetic/base", "base_revision": "b" * 40, "lora": 16, "head_dim": 256,
        "option_isolation": 0, "special_embeddings": 0, "lora_targets": "all", "weights_dtype": "fp32", "full_ft": 0}})
    state.request = {"schema_version": "kev-training-request/v1", "intent": "prepare_training",
        "source": {"agent_id": "synthetic-agent", "parent_experiment_id": "synthetic-exp", "parent_ref": "git:" + "a" * 40, "source_run_ids": ["synthetic-run"]},
        "dataset": {"directory": str(state.data), "kind": "trace-ir"},
        "checkpoint": {"init_from": "synthetic/checkpoint@" + "c" * 40, "training_config_path": str(state.config), "training_config_sha256": planner.digest(state.config)},
        "environment": {"kev_root": str(state.root / "kev"), "run_root": str(state.root / "job"), "server_id": "synthetic-server", "credential_ref": "ref:synthetic/key"},
        "training": {"calibration_folds": 2}}
    state.request_path = state.root / "request.json"
    planner.write_json(state.request_path, state.request)
    return state


class TestTrainingPlan:
    def test_public_dependency_is_explicit_and_help_does_not_load_it(self):
        with patch.dict(os.environ, {"HARNESS_PROGRAM_ROOT": ""}):
            with pytest.raises(ValueError, match="HARNESS_PROGRAM_ROOT"):
                planner.reporting()
            with contextlib.redirect_stdout(io.StringIO()), pytest.raises(SystemExit) as ended:
                planner.main(["--help"])
            assert (ended.value.code) == (0)

    @pytest.fixture(autouse=True)
    def setup(self, training_state):
        self.__dict__.update(vars(training_state))

    def build(self):
        planner.write_json(self.request_path, self.request)
        return planner.build_plan(self.request, self.request_path)

    def test_recipe_uses_only_train_without_changing_candidates(self):
        plan = self.build(); args = plan["commands"]["train"]["argv"]
        assert (args[args.index("--data") + 1]) == (str(self.data / "train.jsonl"))
        for option in ("p_none", "p_none_distract", "p_distract", "p_none_pair"):
            assert (args[args.index("--" + option) + 1]) == ("0")
        assert ("--suite") not in (args); assert ("--replay") not in (args)
        assert (plan["execution"]["training"]) == ("not_run")
        assert not ((self.root / "job").exists())

    def test_default_recipe_remains_cuda_bf16_lora(self):
        plan = self.build()
        train = plan["commands"]["train"]
        assert (plan["training"]["recipe"]) == ("cuda-bf16-lora")
        assert (train["argv"][train["argv"].index("--dtype") + 1]) == ("bf16")
        assert ("CUDA/bf16/VRAM-checked") in (train["requires"])
        # Older plans did not carry a recipe name; their BF16 command stays valid.
        del plan["training"]["recipe"]
        assert (planner.training_recipe(plan)) == ("cuda-bf16-lora")

    def test_explicit_fp32_recipe_preserves_lora_budgets_and_augmentation(self):
        self.request["training"]["recipe"] = "cuda-fp32-lora"
        plan = self.build()
        train = plan["commands"]["train"]
        args = train["argv"]
        assert (planner.training_recipe(plan)) == ("cuda-fp32-lora")
        for option, expected in (("dtype", "fp32"), ("weights_dtype", "fp32"), ("device", "cuda"),
                                 ("epochs", "1"), ("lr", "2e-05"), ("batch", "1"), ("accum", "8"),
                                 ("checkpointing", "1"), ("max_state", "384")):
            assert (args[args.index("--" + option) + 1]) == (expected)
        assert ("CUDA/fp32/VRAM-checked") in (train["requires"])
        assert ("CUDA/bf16/VRAM-checked") not in (train["requires"])
        assert (plan["context_limits"]) == ({"max_state": 384, "max_branch": 1024, "max_packed": 2048})
        assert (plan["augmentation"]) == ({"p_none": 0, "p_none_distract": 0, "p_distract": 0,
                                               "p_none_pair": 0, "choice_shuffle": True})
        assert (any("cuda-fp32-lora" in warning and "CUDA/fp32" in warning for warning in plan["warnings"]))
        assert ("--full_ft") not in (args)
        assert (plan["execution"]["training"]) == ("not_run")

    def test_fp32_recipe_cannot_retain_bf16_backbone_weights(self):
        config = planner.read_json(self.config)
        config["args"]["weights_dtype"] = "bf16"
        planner.write_json(self.config, config)
        self.request["checkpoint"]["training_config_sha256"] = planner.digest(self.config)
        assert (self.build()["checkpoint"]["weights_dtype"]) == ("bf16")
        self.request["training"]["recipe"] = "cuda-fp32-lora"
        with pytest.raises(ValueError, match="fp32_recipe_requires_fp32_checkpoint_weights"):
            self.build()

    @pytest.mark.parametrize('case_index_1', range(4))
    @pytest.mark.parametrize('case_index_2', range(7))
    def test_recipe_rejects_argparse_overrides_and_noncanonical_options(self, case_index_1, case_index_2):
        self.request['training']['recipe'] = 'cuda-fp32-lora'
        plan = self.build()
        parser = argparse.ArgumentParser()
        parser.add_argument('--dtype')
        parser.add_argument('--device')
        parser.add_argument('--weights_dtype')
        (override, field, actual) = tuple(((['--dtype=bf16'], 'dtype', 'bf16'), (['--dty', 'bf16'], 'dtype', 'bf16'), (['--weights_dtype=bf16'], 'weights_dtype', 'bf16'), (['--device=cpu'], 'device', 'cpu')))[case_index_1]
        changed = deepcopy(plan)
        changed['commands']['train']['argv'] += override
        (parsed, _) = parser.parse_known_args(changed['commands']['train']['argv'][5:])
        assert getattr(parsed, field) == actual
        with pytest.raises(ValueError, match='training_recipe_command_mismatch'):
            planner.training_recipe(changed)
        override = tuple((['--dtype', 'fp32'], ['--dtype=fp32'], ['--max_state=8192'], ['--init_from=other/checkpoint'], ['--checkpointing', '0'], ['--full_ft', '1'], ['--']))[case_index_2]
        changed = deepcopy(plan)
        changed['commands']['train']['argv'] += override
        with pytest.raises(ValueError, match='training_recipe_command_mismatch'):
            planner.training_recipe(changed)

    @pytest.mark.parametrize('case_index_1', range(4))
    def test_unsupported_recipe_and_conflicting_dtype_are_rejected(self, case_index_1):
        recipe = tuple(('cuda-fp16-lora', 'cpu-fp32-lora', None, []))[case_index_1]
        self.request['training']['recipe'] = recipe
        with pytest.raises(ValueError, match='unsupported_training_recipe'):
            self.build()
        self.request['training'] = {'recipe': 'cuda-bf16-lora', 'dtype': 'fp32'}
        with pytest.raises(ValueError, match='training_recipe_dtype_mismatch'):
            self.build()

    def test_plan_only_cannot_be_promoted_to_training_preparation(self):
        self.request["intent"] = "plan_only"
        with pytest.raises(ValueError, match="plan_only"):
            self.build()

    def test_legacy_fp32_plan_keeps_its_precision(self):
        self.request["training"]["dtype"] = "fp32"
        plan = self.build()
        plan["training"].pop("recipe")
        assert (planner.training_recipe(plan)) == ("cuda-fp32-lora")
        plan["commands"]["train"]["argv"].extend(["--dtype=bf16"])
        with pytest.raises(ValueError, match="training_recipe_command_mismatch"):
            planner.training_recipe(plan)

    def test_precision_is_explicit_without_changing_default_or_weights(self):
        args = self.build()["commands"]["train"]["argv"]
        assert (args[args.index("--dtype") + 1]) == ("bf16")
        self.request["training"]["dtype"] = "fp32"
        card = self.build()["commands"]["train"]
        assert (card["argv"][card["argv"].index("--dtype") + 1]) == ("fp32")
        assert ("CUDA/fp32/VRAM-checked") in (card["requires"])
        assert (card["argv"][card["argv"].index("--weights_dtype") + 1]) == ("fp32")
        self.request["training"]["dtype"] = "fp16"
        with pytest.raises(ValueError, match="invalid_training_dtype"):
            self.build()
        self.request["training"]["dtype"] = "fp32"
        config = planner.read_json(self.config); config["args"]["weights_dtype"] = "bf16"
        planner.write_json(self.config, config)
        self.request["checkpoint"]["training_config_sha256"] = planner.digest(self.config)
        with pytest.raises(ValueError, match="fp32_checkpoint_weights"):
            self.build()

    def test_trace_sources_cannot_be_replaced_with_empty_run_ids(self):
        self.request["source"]["source_run_ids"] = []
        with pytest.raises(ValueError, match="real_source_run_ids_required"):
            self.build()

    def test_prepare_cli_is_readable_and_preserves_machine_plan(self):
        output = self.root / "prepared-human"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = planner.main(["prepare", "--request", str(self.request_path), "--out", str(output)])
        assert (result) == (0)
        assert ("训练方案已保存，尚未启动训练") in (stdout.getvalue())
        assert ('"schema_version"') not in (stdout.getvalue())
        assert ("训练集") in ((output / "report.md").read_text())
        assert ("cuda-bf16-lora") in ((output / "report.md").read_text())
        assert (planner.read_json(output / "training-plan.json")["execution"]["training"]) == ("not_run")
        machine_output = self.root / "prepared-json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = planner.main(["prepare", "--request", str(self.request_path), "--out", str(machine_output), "--json"])
        assert (result) == (0)
        assert (json.loads(stdout.getvalue())["training"]) == ("not_run")
        assert ((machine_output / "report.md").is_file())

    def test_fp32_prepare_reports_the_selected_recipe(self):
        self.request["training"]["recipe"] = "cuda-fp32-lora"
        planner.write_json(self.request_path, self.request)
        out = self.root / "prepared-fp32"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = planner.main(["prepare", "--request", str(self.request_path), "--out", str(out), "--json"])
        assert (code) == (0)
        assert (json.loads(stdout.getvalue())["training_recipe"]) == ("cuda-fp32-lora")
        assert ("cuda-fp32-lora") in ((out / "report.md").read_text())


    def test_missing_encoding_report_is_a_readable_failure(self):
        plan = self.build(); pp = self.root / "plan.json"
        planner.write_json(pp, plan)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = planner.main(["commands", "--plan", str(pp), "--encoding-report", str(self.root / "absent.json")])
        assert (code) == (2)
        assert ("当前不能继续") in (stdout.getvalue())
        assert ("尚未启动训练") in (stdout.getvalue())

    def test_reviewed_metadata_does_not_hide_split_overlap(self):
        path = self.data / "test.jsonl"
        rows = [json.loads(s) for s in path.read_text().splitlines()]
        train = json.loads((self.data / "train.jsonl").read_text().splitlines()[0])
        rows[0]["_meta"]["group_id"] = train["_meta"]["group_id"]
        path.write_text("".join(json.dumps(r) + "\n" for r in rows))
        with pytest.raises(ValueError, match="cross_partition_group"):
            self.build()

    def test_different_json_with_same_native_input_cannot_cross_partitions(self):
        native = planner.load_module("synthetic_native_identity", planner.research_root() / "native_input.py")
        train = json.loads((self.data / "train.jsonl").read_text().splitlines()[0])
        path = self.data / "test.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        rows[0]["state"] = native.render(train["state"])
        rows[0]["questions"] = deepcopy(train["questions"])
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        with pytest.raises(ValueError, match="cross_partition_identical_rendered_input"):
            self.build()

    def test_stale_checkpoint_metadata_is_blocked(self):
        self.config.write_text(self.config.read_text() + " ")
        with pytest.raises(ValueError, match="hash_mismatch"):
            self.build()

    def test_full_weight_checkpoint_cannot_enter_lora_recipe(self):
        config = planner.read_json(self.config); config["args"]["full_ft"] = 1
        planner.write_json(self.config, config)
        self.request["checkpoint"]["training_config_sha256"] = planner.digest(self.config)
        with pytest.raises(ValueError, match="full_weight"):
            self.build()

    def test_checkpoint_revision_requires_real_hub_shape(self):
        self.request["checkpoint"]["init_from"] = "unresolvable@" + "c" * 40
        with pytest.raises(ValueError, match="owner_repo"):
            self.build()

    def local_request(self):
        binding = make_snapshot(self.root, self.config, self.request["checkpoint"]["init_from"])
        self.request["checkpoint"]["local_snapshot"] = binding
        return binding

    def test_local_snapshot_preserves_hub_identity_and_binds_native_execution_path(self):
        binding = self.local_request()
        plan = self.build()
        checkpoint = plan["checkpoint"]
        assert (checkpoint["init_from"]) == (self.request["checkpoint"]["init_from"])
        assert (checkpoint["local_snapshot"]) == (binding)
        assert ("files") not in (checkpoint["local_snapshot"]), "逐文件清单只来自固定的仓库元数据引用"
        argv = plan["commands"]["train"]["argv"]
        assert (argv[argv.index("--init_from") + 1]) == (binding["path"])
        assert (planner.verify_checkpoint_source(checkpoint)) == ({
            "init_from": checkpoint["init_from"], "execution_init_from": binding["path"],
            "local_snapshot": binding, "verified_files": 4})
        argv[argv.index("--init_from") + 1] = checkpoint["init_from"]
        with pytest.raises(ValueError, match="training_recipe_command_mismatch"):
            planner.training_recipe(plan)

    def test_local_snapshot_prepare_report_names_identity_and_actual_path(self):
        binding = self.local_request()
        planner.write_json(self.request_path, self.request)
        out, stdout = self.root / "local-plan", io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = planner.main(["prepare", "--request", str(self.request_path), "--out", str(out), "--json"])
        assert (code) == (0)
        result = json.loads(stdout.getvalue())
        assert (result["checkpoint_source"]["init_from"]) == (self.request["checkpoint"]["init_from"])
        assert (result["checkpoint_source"]["execution_init_from"]) == (binding["path"])
        report = (out / "report.md").read_text()
        assert (self.request["checkpoint"]["init_from"]) in (report)
        assert (binding["path"]) in (report)

    def test_local_snapshot_rejects_missing_weights_and_changed_bytes(self):
        binding = self.local_request()
        path = Path(binding["path"]) / "adapter_model.safetensors"
        original = path.read_bytes()
        path.write_bytes(original[:-1] + b"!")
        with pytest.raises(ValueError, match="local_snapshot_file_hash_mismatch"):
            self.build()
        path.unlink()
        with pytest.raises(ValueError, match="local_snapshot_file_missing"):
            self.build()

    @pytest.mark.parametrize('case_index_1', range(2))
    def test_local_snapshot_repository_id_and_revision_must_match_fixed_source(self, case_index_1):
        binding = self.local_request()
        path = Path(binding['repository_metadata_path'])
        original = planner.read_json(path)
        changed = tuple(({'id': 'other/checkpoint'}, {'sha': 'd' * 40}))[case_index_1]
        planner.write_json(path, {**original, **changed})
        binding['repository_metadata_sha256'] = planner.digest(path)
        with pytest.raises(ValueError, match='local_snapshot_source_identity_mismatch'):
            self.build()

    def test_local_snapshot_metadata_and_training_config_are_both_bound(self):
        binding = self.local_request()
        path = Path(binding["repository_metadata_path"])
        path.write_text(path.read_text() + "\n")
        with pytest.raises(ValueError, match="local_snapshot_repository_metadata_changed"):
            self.build()
        binding["repository_metadata_sha256"] = planner.digest(path)
        # 另一份独立 metadata 即便自己摘要正确，也不能替代快照中的 training_config。
        config = planner.read_json(self.config)
        config["args"]["head_dim"] = 128
        planner.write_json(self.config, config)
        self.request["checkpoint"]["training_config_sha256"] = planner.digest(self.config)
        with pytest.raises(ValueError, match="local_snapshot_training_config_mismatch"):
            self.build()

    def test_local_snapshot_requires_complete_fixed_repository_metadata(self):
        binding = self.local_request()
        path = Path(binding["repository_metadata_path"])
        metadata = planner.read_json(path)
        metadata["siblings"] = [row for row in metadata["siblings"] if row["rfilename"] != "head.pt"]
        planner.write_json(path, metadata)
        binding["repository_metadata_sha256"] = planner.digest(path)
        with pytest.raises(ValueError, match="local_snapshot_checkpoint_incomplete"):
            self.build()

    def test_local_snapshot_command_release_rechecks_files_and_encoding_source_identity(self):
        binding = self.local_request()
        plan = self.build()
        pp, rp = self.root / "plan.json", self.root / "encoding.json"
        planner.write_json(pp, plan)
        report = {"schema_version": "kev-encoding-report/v1", "status": "ready", "plan_sha256": planner.digest(pp),
                  "training_recipe": plan["training"]["recipe"], "kev_commit": plan["kev_commit"],
                  "base": plan["checkpoint"]["base"], "base_revision": plan["checkpoint"]["base_revision"],
                  "failures": [], "checks": {name: "passed" for name in ("metadata", "native_imports", "tokenizer", "native_loader", "native_materialize",
                      "strict_encoding", "native_fits", "target_mapping", "choice_shuffle", "final_identity_recheck")},
                  "checked_records": sum(x["records"] for x in plan["dataset"]["files"].values()), "files": deepcopy(plan["dataset"]["files"]),
                  "tokenstats": {"limits": dict(planner.LIMITS), "partitions": {name: {"checked_records": x["records"]} for name, x in plan["dataset"]["files"].items()}}}
        planner.write_json(rp, report)
        with pytest.raises(ValueError, match="encoding_checkpoint_source_mismatch"):
            planner.authorized_training_card(pp, rp)
        report["checkpoint_source"] = planner.verify_checkpoint_source(plan["checkpoint"])
        planner.write_json(rp, report)
        released = planner.authorized_training_card(pp, rp)
        assert (released["checkpoint_source"]["init_from"]) == (plan["checkpoint"]["init_from"])
        assert (released["checkpoint_source"]["execution_init_from"]) == (binding["path"])
        weights = Path(binding["path"]) / "head.pt"
        raw = weights.read_bytes(); weights.write_bytes(raw[:-1] + b"!")
        with pytest.raises(ValueError, match="local_snapshot_file_hash_mismatch"):
            planner.authorized_training_card(pp, rp)

    def test_calibration_report_does_not_claim_persisted_temperature(self):
        plan = self.build()
        assert ("calibration-write") not in (plan["commands"])
        assert ("report-only-does-not-write-checkpoint-temperature") in (plan["commands"]["calibration-report"]["requires"])
        self.request["training"]["calibration_policy"] = "workload_heldout"
        plan = self.build()
        assert ("--allow-in-distribution") in (plan["commands"]["calibration-write"]["argv"])
        assert ("calibration-raw/rows.json") in (" ".join(plan["commands"]["calibration-write"]["argv"]))
        assert (str(self.data / "test.jsonl")) not in (plan["commands"]["calibration-write"]["argv"])

    def test_final_test_is_separate_and_predictor_environment_is_fixed(self):
        plan = self.build()
        final = plan["commands"]["final-test"]
        assert ("independent-final-acceptance-authorized") in (final["requires"])
        assert ("KEV_TEMPERATURE") in (final["unset_env"])
        assert (final["env"]["KEV_LORA_SCALE"]) == ("1")
        assert (final["env"]["KEV_BACKEND"]) == ("torch")
        assert ("KEV_MERGE") in (final["unset_env"])

    @pytest.mark.parametrize('case_index_1', range(7))
    def test_explicit_execution_environment_reaches_every_phase_without_changing_recipe(self, case_index_1):
        self.request['training'].update(recipe='cuda-fp32-lora', calibration_policy='workload_heldout')
        previous = self.build()
        environment = {'HF_HUB_CACHE': str(self.root / 'hub'), 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'USE_HUB_KERNELS': 'NO', 'UV_PROJECT_ENVIRONMENT': str(self.root / 'venv'), 'UV_NO_SYNC': '1'}
        self.request['environment']['env'] = environment
        plan = self.build()
        assert plan['environment']['env'] == environment
        assert 'env' not in previous['environment']
        assert len(plan['commands']) == 7
        (name, command) = tuple(plan['commands'].items())[case_index_1]
        assert command['env'] == {**environment, **previous['commands'][name]['env']}
        assert command['argv'] == [str(self.root / 'venv/bin/uv'), *previous['commands'][name]['argv'][1:]]
        for key in ('cwd', 'unset_env', 'requires'):
            assert command[key] == previous['commands'][name][key]
        assert planner.training_recipe(plan) == 'cuda-fp32-lora'
        assert plan['context_limits'] == previous['context_limits']
        assert plan['checkpoint'] == previous['checkpoint']
        assert plan['augmentation'] == previous['augmentation']
        plan['commands']['train']['env']['HF_HUB_OFFLINE'] = '0'
        assert plan['commands']['calibration-raw']['env']['HF_HUB_OFFLINE'] == '1'
        assert self.request['environment']['env'] == environment

    def test_phase_environment_takes_precedence_and_does_not_drop_unsets(self):
        self.request["environment"]["env"] = {"HF_HUB_OFFLINE": "1"}
        baseline = self.build()
        original = planner.card

        def phase_card(cwd, argv, **kwargs):
            result = original(cwd, argv, **kwargs)
            # 阶段给定同名环境时必须优先，不能被共享执行环境反向覆盖。
            if "kev.benchmark" in argv:
                result["env"]["HF_HUB_OFFLINE"] = "0"
            return result

        with patch.object(planner, "card", side_effect=phase_card):
            plan = self.build()
        assert (plan["commands"]["train"]["env"]["HF_HUB_OFFLINE"]) == ("1")
        for name in ("calibration-raw", "development-raw", "final-test"):
            assert (plan["commands"][name]["env"]["HF_HUB_OFFLINE"]) == ("0")
            assert (plan["commands"][name]["unset_env"]) == (baseline["commands"][name]["unset_env"])
        assert ("KEV_TEMPERATURE") in (plan["commands"]["final-test"]["unset_env"])
        assert (plan["commands"]["final-test"]["env"]["KEV_DTYPE"]) == ("fp32")

    @pytest.mark.parametrize('case_index_1', range(14))
    def test_execution_environment_rejects_invalid_types_paths_switches_and_semantic_overrides(self, case_index_1):
        environment = tuple((None, [], 'offline', {'HF_HUB_OFFLINE': True}, {'HF_HUB_OFFLINE': 'true'}, {'USE_HUB_KERNELS': 'UNIT_PRIVATE_VALUE'}, {'HF_HUB_CACHE': 'relative/cache'}, {'UV_PROJECT_ENVIRONMENT': '/venv\nUNIT_PRIVATE_VALUE'}, {'KEV_DTYPE': 'bf16'}, {'KEV_BASE_REVISION': 'd' * 40}, {'KEV_MAX_STATE': '8192'}, {'HOME': '/other-home'}, {'PATH': '/other-bin'}, {'UV_ENV_FILE': '/credentials'}))[case_index_1]
        self.request['environment']['env'] = environment
        with pytest.raises(ValueError) as caught:
            self.build()
        assert 'UNIT_PRIVATE_VALUE' not in str(caught.value)

    @pytest.mark.parametrize('case_index_1', range(5))
    def test_secret_environment_is_rejected_without_copying_values_to_cli_reports(self, case_index_1):
        private = 'UNIT_ONLY_PRIVATE_VALUE'
        key = tuple(('HF_TOKEN', 'OPENAI_API_KEY', 'SSH_PASSWORD', 'API_KEY', 'TOKEN'))[case_index_1]
        self.request['environment']['env'] = {key: private}
        planner.write_json(self.request_path, self.request)
        output = self.root / ('blocked-' + key)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = planner.main(['prepare', '--request', str(self.request_path), '--out', str(output), '--json'])
        assert result == 2
        assert not (output / 'training-plan.json').exists()
        assert private not in stdout.getvalue()
        for file in output.iterdir():
            assert private not in file.read_text()

    def test_changed_execution_environment_requires_a_new_encoding_report(self):
        self.request["environment"]["env"] = {"UV_NO_SYNC": "1"}
        plan = self.build(); pp = self.root / "plan.json"; rp = self.root / "encoding.json"
        planner.write_json(pp, plan)
        planner.write_json(rp, {"schema_version": "kev-encoding-report/v1", "status": "ready", "plan_sha256": planner.digest(pp)})
        plan["environment"]["env"]["UV_NO_SYNC"] = "0"
        plan["commands"]["train"]["env"]["UV_NO_SYNC"] = "0"
        planner.write_json(pp, plan)
        with pytest.raises(ValueError, match="encoding_report_plan_mismatch"):
            planner.authorized_training_card(pp, rp)

    def test_encoding_report_must_bind_the_exact_plan_and_files(self):
        plan = self.build(); pp = self.root / "plan.json"; rp = self.root / "encoding.json"
        planner.write_json(pp, plan)
        report = {"schema_version": "kev-encoding-report/v1", "status": "ready", "plan_sha256": "d" * 64,
                  "kev_commit": plan["kev_commit"], "base": plan["checkpoint"]["base"], "base_revision": plan["checkpoint"]["base_revision"]}
        planner.write_json(rp, report)
        with pytest.raises(ValueError, match="plan_mismatch"):
            planner.authorized_training_card(pp, rp)
        report["plan_sha256"] = planner.digest(pp); planner.write_json(rp, report)
        with pytest.raises(ValueError, match="native_checks_incomplete"):
            planner.authorized_training_card(pp, rp)
        # A complete synthetic receipt exercises only the command-release gate,
        # never asserts that native tokenization actually ran in this unit test.
        report.update(failures=[], checks={name: "passed" for name in ("metadata", "native_imports", "tokenizer", "native_loader", "native_materialize",
                      "strict_encoding", "native_fits", "target_mapping", "choice_shuffle", "final_identity_recheck")},
                      checked_records=sum(x["records"] for x in plan["dataset"]["files"].values()), files=deepcopy(plan["dataset"]["files"]),
                      tokenstats={"limits": dict(planner.LIMITS), "partitions": {name: {"checked_records": x["records"]} for name, x in plan["dataset"]["files"].items()}})
        planner.write_json(rp, report)
        assert (planner.authorized_training_card(pp, rp)["status"]) == ("encoding_ready_execution_not_started")
        p = self.data / "train.jsonl"; p.write_text(p.read_text() + "\n")
        with pytest.raises(ValueError, match="changed_after_encoding"):
            planner.authorized_training_card(pp, rp)

    def test_credentials_are_not_plan_fields(self):
        self.request["environment"]["password"] = "synthetic-non-secret"
        with pytest.raises(ValueError, match="credentials"):
            self.build()

    @pytest.mark.parametrize('case_index_1', range(2))
    def test_fp32_command_release_checks_recipe_and_legacy_plan_binding(self, case_index_1):
        self.request['training']['recipe'] = 'cuda-fp32-lora'
        self.request['environment']['env'] = {'HF_HUB_OFFLINE': '1', 'UV_NO_SYNC': '1', 'UV_PROJECT_ENVIRONMENT': str(self.root / 'venv')}
        plan = self.build()
        pp = self.root / 'plan.json'
        rp = self.root / 'encoding.json'
        planner.write_json(pp, plan)
        report = {'schema_version': 'kev-encoding-report/v1', 'status': 'ready', 'plan_sha256': planner.digest(pp), 'kev_commit': plan['kev_commit'], 'base': plan['checkpoint']['base'], 'base_revision': plan['checkpoint']['base_revision'], 'failures': [], 'checks': {name: 'passed' for name in ('metadata', 'native_imports', 'tokenizer', 'native_loader', 'native_materialize', 'strict_encoding', 'native_fits', 'target_mapping', 'choice_shuffle', 'final_identity_recheck')}, 'checked_records': sum((x['records'] for x in plan['dataset']['files'].values())), 'files': deepcopy(plan['dataset']['files']), 'tokenstats': {'limits': dict(planner.LIMITS), 'partitions': {name: {'checked_records': x['records']} for (name, x) in plan['dataset']['files'].items()}}}
        recipe = tuple((None, 'cuda-bf16-lora'))[case_index_1]
        if recipe is not None:
            report['training_recipe'] = recipe
        planner.write_json(rp, report)
        with pytest.raises(ValueError, match='encoding_training_recipe_mismatch'):
            planner.authorized_training_card(pp, rp)
        report['training_recipe'] = 'cuda-fp32-lora'
        planner.write_json(rp, report)
        result = planner.authorized_training_card(pp, rp)
        assert result['training_recipe'] == 'cuda-fp32-lora'
        assert result['command']['env'] == self.request['environment']['env']
        assert 'CUDA/fp32/VRAM/budget' in result['remaining'][0]
        plan['training']['dtype'] = 'fp32'
        del plan['training']['recipe']
        planner.write_json(pp, plan)
        report['plan_sha256'] = planner.digest(pp)
        del report['training_recipe']
        planner.write_json(rp, report)
        assert planner.authorized_training_card(pp, rp)['training_recipe'] == 'cuda-fp32-lora'
        report['training_recipe'] = 'cuda-bf16-lora'
        planner.write_json(rp, report)
        with pytest.raises(ValueError, match='encoding_training_recipe_mismatch'):
            planner.authorized_training_card(pp, rp)
        plan['commands']['train']['argv'][plan['commands']['train']['argv'].index('--dtype') + 1] = 'bf16'
        planner.write_json(pp, plan)
        with pytest.raises(ValueError, match='encoding_report_plan_mismatch'):
            planner.authorized_training_card(pp, rp)

    @pytest.mark.parametrize('case_index_1', range(5))
    def test_selected_venv_binds_uv_for_all_stage_cards_without_path_override(self, case_index_1):
        venv = str(self.root / 'task venv')
        self.request['environment']['env'] = {'UV_PROJECT_ENVIRONMENT': venv, 'UV_NO_SYNC': '1'}
        plan = self.build()
        (name, command) = tuple(plan['commands'].items())[case_index_1]
        assert command['argv'][:3] == [str(Path(venv) / 'bin/uv'), 'run', 'python']
        assert 'PATH' not in command['env']
        assert planner.training_recipe(plan) == plan['training']['recipe']
        plan['commands']['train']['argv'][0] = 'uv'
        with pytest.raises(ValueError, match='training_recipe_command_mismatch'):
            planner.training_recipe(plan)

    def test_no_selected_venv_preserves_native_uv_resolution(self):
        plan = self.build()
        assert (all(command["argv"][:3] == ["uv", "run", "python"] for command in plan["commands"].values()))

    def test_fold_count_uses_independent_groups(self):
        self.request["training"]["calibration_folds"] = 100
        with pytest.raises(ValueError, match="independent_groups"):
            self.build()
