from src.utils.help_generator import KickstartHelpGenerator


def test_generate_examples_includes_rust_service_and_lib(monkeypatch):
    generator = KickstartHelpGenerator()

    monkeypatch.setattr(generator, "get_available_languages", lambda: ["python", "rust"])
    monkeypatch.setattr(generator, "get_available_project_types", lambda: ["service", "lib"])

    examples = generator.generate_examples()

    assert examples == [
        "kickstart create service my-api --lang python",
        "kickstart create service my-api --lang rust",
        "kickstart create lib my-utils --lang rust --gh",
    ]
