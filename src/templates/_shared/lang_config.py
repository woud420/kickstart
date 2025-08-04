"""Language-specific configuration for templates."""

from typing import Dict, Any

LANGUAGE_CONFIG: Dict[str, Dict[str, Any]] = {
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
        ]
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
        ]
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
        ]
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
        ]
    },
    "java": {
        "main_ext": "java",
        "config_file": "pom.xml",
        "dependency_file": "pom.xml", 
        "build_tool": "maven",
        "test_framework": "junit",
        "gitignore_patterns": [
            "target/",
            "*.class",
            "*.jar",
            "*.war",
            "*.ear",
            ".mvn/",
        ]
    },
    "node": {
        "main_ext": "js",
        "config_file": "package.json",
        "dependency_file": "package.json",
        "build_tool": "npm",
        "test_framework": "jest",
        "gitignore_patterns": [
            "node_modules/",
            "npm-debug.log*",
            "yarn-debug.log*",
            "yarn-error.log*",
            ".npm",
            ".yarn-integrity",
            "*.tgz",
            "*.tar.gz",
        ]
    }
}


def get_language_config(language: str) -> Dict[str, Any]:
    """Get configuration for a specific language."""
    return LANGUAGE_CONFIG.get(language, {})


def get_supported_languages() -> list[str]:
    """Get list of supported languages."""
    return list(LANGUAGE_CONFIG.keys())