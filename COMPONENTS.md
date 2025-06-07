# Kickstart Component Format

Kickstart accepts a simple Markdown manifest describing the components you want
to create. Each component type has its own heading followed by bullet list
entries.

## Keys
- `name` – unique name for services or frontends
- `root` – directory where the component is created
- `lang` – optional language for a service (defaults to the CLI's chosen value)

## Example
```markdown
## services
- name: user-service
  lang: python
  root: services/user-service

## frontends
- name: dashboard
  root: apps/dashboard

## monorepo
- root: platform
```
