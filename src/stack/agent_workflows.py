"""Agent workflow artifact registry."""

from dataclasses import dataclass

from src.stack.types import TemplateConfig


@dataclass(frozen=True)
class AgentWorkflowArtifact:
    """Generated artifact that documents agent workflow guidance."""

    id: str
    target: str
    template: str
    description: str

    def template_config(self) -> TemplateConfig:
        """Return the template config used to render this artifact."""
        return TemplateConfig(self.target, self.template)


agent_workflow_artifacts: dict[str, AgentWorkflowArtifact] = {
    "recommended-agents": AgentWorkflowArtifact(
        id="recommended-agents",
        target="docs/agents/recommended-agents.md",
        template="agents_recommended.md",
        description="Recommended local agents and skills for scaffolded projects.",
    ),
}


def agent_workflow_template_configs() -> tuple[TemplateConfig, ...]:
    """Return template configs for generated agent workflow artifacts."""
    return tuple(artifact.template_config() for artifact in agent_workflow_artifacts.values())
