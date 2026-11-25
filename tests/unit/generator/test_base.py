import pytest
import json
from src.generator.base import BaseGenerator
from src.generator.scaffold_contract import ScaffoldArtifacts, ScaffoldContract
from unittest.mock import patch

@pytest.fixture
def base_generator():
    return BaseGenerator("test-project", {"key": "value"})

def test_create_directories(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        directories = ["dir1", "dir2/subdir"]
        base_generator.create_directories(directories)
        assert (tmp_path / "dir1").exists()
        assert (tmp_path / "dir2/subdir").exists()

def test_init_basic_structure(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        base_generator.init_basic_structure(["foo", "bar"])
        assert (tmp_path / "foo").exists()
        assert (tmp_path / "bar").exists()

def test_create_architecture_docs(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        contract = ScaffoldContract(
            project_kind="service",
            language="python", framework="minimal",
            execution_models=("container",),
            runtime_platforms=("local",),
            entrypoint="src/main.py",
        )
        base_generator.create_architecture_docs("My Docs", ["src/routes", "src/clients"], contract)
        arch = tmp_path / "docs/architecture/README.md"
        assert arch.exists()
        content = arch.read_text()
        assert content.startswith("<!-- kickstart:begin architecture-readme -->\n# My Docs\n")
        assert content.endswith("<!-- kickstart:end architecture-readme -->\n")
        assert "`src/routes/` — HTTP surface" in content
        assert "Entrypoint: `src/main.py`" in content

def test_claude_skills_link_degrades_to_pointer_file(base_generator, tmp_path, monkeypatch):
    def _no_symlinks(*args, **kwargs):
        raise OSError("symlinks unsupported")

    monkeypatch.setattr("src.generator.base.os.symlink", _no_symlinks)
    with patch.object(base_generator, 'project', tmp_path):
        assert base_generator._create_claude_skills_link()
        pointer = tmp_path / ".claude" / "skills"
        assert not pointer.is_symlink()
        # Exact git-materialized symlink shape: POSIX separators, no newline.
        assert pointer.read_text() == "../.agents/skills"


def test_create_scaffold_contract_docs(base_generator, tmp_path):
    with patch.object(base_generator, 'project', tmp_path):
        contract = ScaffoldContract(
            project_kind="service",
            language="python", framework="minimal",
            execution_models=("container",),
            runtime_platforms=("local",),
            artifacts=ScaffoldArtifacts(image="dockerfile"),
        )

        base_generator.create_scaffold_contract_docs(contract)

        assert (tmp_path / "AGENTS.md").exists()
        assert (tmp_path / "docs/contracts/README.md").exists()
        assert (tmp_path / "docs/operations/README.md").exists()
        assert (tmp_path / "docs/decisions/README.md").exists()
        manifest = json.loads((tmp_path / ".kickstart/scaffold.json").read_text())
        assert manifest["schema_version"] == "4.0"
        assert manifest["project"] == {
            "name": "test-project",
            "kind": "service",
            "language": "python",
            "framework": "minimal",
            "repo_layout": "single-project",
        }
        assert manifest["execution"] == {"models": ["container"], "platforms": ["local"]}
        assert manifest["artifacts"] == {"image": "dockerfile"}
        assert manifest["provider"] == {"targets": []}
        assert manifest["extensions"] == {}

def test_write_template_renders_project_toolchain_and_caller_values(tmp_path):
    from src.stack.toolchain_versions import BUN_VERSION

    generator = BaseGenerator("demo_app", {}, root=str(tmp_path))
    generator.template_dir = tmp_path / "templates"
    generator.template_dir.mkdir()
    (generator.template_dir / "summary.tpl").write_text(
        "{{ service_name }}|{{ package_name }}|{{ bun_version }}|{{ label }}"
    )

    assert generator.write_template("out/summary.txt", "summary.tpl", label="custom")
    output = tmp_path / "demo_app" / "out" / "summary.txt"
    assert output.read_text() == f"demo_app|demo-app|{BUN_VERSION}|custom"


def test_write_template_renders_absolute_filename(tmp_path):
    generator = BaseGenerator("demo", {}, root=str(tmp_path))
    template = tmp_path / "greeting.tpl"
    template.write_text("Hello {{ service_name }}")

    assert generator.write_template("greeting.txt", str(template))
    assert (generator.project / "greeting.txt").read_text() == "Hello demo"


def test_write_template_rejects_missing_absolute_filename(tmp_path):
    generator = BaseGenerator("demo", {}, root=str(tmp_path))
    missing = tmp_path / "missing.tpl"

    assert generator.write_template("greeting.txt", str(missing)) is False
    assert not (generator.project / "greeting.txt").exists()


def test_replace_template_preserves_output_when_absolute_source_is_invalid_utf8(tmp_path):
    generator = BaseGenerator("demo", {}, root=str(tmp_path))
    template = tmp_path / "greeting.tpl"
    template.write_text("Hello {{ service_name }}", encoding="utf-8")
    assert generator.write_template("greeting.txt", str(template))

    template.write_bytes(b"broken\xff")
    assert generator.replace_template("greeting.txt", str(template)) is False
    assert (generator.project / "greeting.txt").read_text(encoding="utf-8") == "Hello demo"
