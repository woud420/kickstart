# Weekly dependency update PRs. Minor and patch updates are grouped per
# ecosystem; major updates arrive one per PR.
version: 2
updates:
{% for ecosystem in dependabot_package_ecosystems %}
  - package-ecosystem: {{ ecosystem }}
    directory: /
    schedule:
      interval: weekly
    groups:
      {{ ecosystem }}-minor-and-patch:
        update-types: [minor, patch]

{% endfor %}
{% if dependabot_docker %}
  - package-ecosystem: docker
    directory: /
    schedule:
      interval: weekly

{% endif %}
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
    groups:
      github-actions:
        patterns: ["*"]
