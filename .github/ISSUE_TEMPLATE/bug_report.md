name: Bug report
description: Report something that is not working as expected
labels: ["bug"]
body:
  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear description of the problem. Include the diagnostic code (e.g. E201) if the compiler produced one.
    validations:
      required: true

  - type: textarea
    id: reproduction
    attributes:
      label: Steps to reproduce
      description: The workflow and tool files involved, and the command you ran.
      placeholder: |
        flowspec compile workflow.yaml
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      description: What you expected to happen instead.
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: FlowSpec version, Python version, operating system.
      placeholder: |
        FlowSpec: 0.1.0.dev0
        Python: 3.11.9
        OS: Windows 11
    validations:
      required: true
