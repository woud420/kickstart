"""Language-specific configuration for templates."""

from typing import Never, TypedDict


class LanguageTemplateConfig(TypedDict):
    """Language-specific template metadata."""

    main_ext: str
    config_file: str
    dependency_file: str
    build_tool: str
    test_framework: str
    gitignore_patterns: list[str]


EMPTY_LANGUAGE_CONFIG: dict[str, Never] = {}

LANGUAGE_CONFIG: dict[str, LanguageTemplateConfig] = {
    "python": {
        "main_ext": "py",
        "config_file": "pyproject.toml",
        "dependency_file": "requirements.txt",
        "build_tool": "poetry",
        "test_framework": "pytest",
        "gitignore_patterns": [
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            "build/",
            "develop-eggs/",
            "dist/",
            "downloads/",
            "eggs/",
            ".eggs/",
            "lib/",
            "lib64/",
            "parts/",
            "sdist/",
            "var/",
            "wheels/",
            "*.egg-info/",
            ".installed.cfg",
            "*.egg",
            ".venv/",
            "venv/",
            "ENV/",
            "env/",
        ],
    },
    "rust": {
        "main_ext": "rs",
        "config_file": "Cargo.toml",
        "dependency_file": "Cargo.toml",
        "build_tool": "cargo",
        "test_framework": "cargo test",
        "gitignore_patterns": [
            "target/",
            "Cargo.lock",
            "*.pdb",
        ],
    },
    "go": {
        "main_ext": "go",
        "config_file": "go.mod",
        "dependency_file": "go.mod",
        "build_tool": "go",
        "test_framework": "go test",
        "gitignore_patterns": [
            "# Binaries",
            "bin/",
            "*.exe",
            "*.out",
            "*.test",
            "# Go modules",
            "go.sum",
        ],
    },
    "typescript": {
        "main_ext": "ts",
        "config_file": "package.json",
        "dependency_file": "package.json",
        "build_tool": "bun",
        "test_framework": "vitest",
        "gitignore_patterns": [
            "node_modules/",
            "dist/",
            "coverage/",
            "bun-debug.log*",
        ],
    },
    "cpp": {
        "main_ext": "cpp",
        "config_file": "CMakeLists.txt",
        "dependency_file": "CMakeLists.txt",
        "build_tool": "cmake",
        "test_framework": "ctest",
        "gitignore_patterns": [
            "build/",
            "*.o",
            "*.a",
            "*.so",
            "*.exe",
            "CMakeCache.txt",
            "CMakeFiles/",
            "cmake_install.cmake",
        ],
    },
}


def get_language_config(language: str) -> LanguageTemplateConfig | dict[str, Never]:
    """Get configuration for a specific language."""
    return LANGUAGE_CONFIG.get(language, EMPTY_LANGUAGE_CONFIG)


def get_supported_languages() -> list[str]:
    """Get list of supported languages."""
    return list(LANGUAGE_CONFIG.keys())
