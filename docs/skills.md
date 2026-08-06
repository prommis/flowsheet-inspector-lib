---
title: PrOMMiS Agent Skills
---
# PrOMMiS Agent Skills

This repository contains agent skills that help Codex work with PrOMMiS,
IDAES, WaterTAP, Pyomo, and Flowsheet Inspector flowsheets. The skills can
prepare flowsheets for the Flowsheet Inspector, change fixed values, find
imports, and explain solver or diagnostics issues.

The following setup works on Windows, macOS, and Linux.

## Prerequisites

Before installing the skills, install:

- [Git](https://git-scm.com/downloads)
- Codex with plugin support

Open a terminal and check that both commands are available:

```{code} shell
git --version
codex plugin --help
```

If either command is not found, install or update that program before
continuing.

## Install the skills

### 1. Download the repository

In a terminal, run:

```{code} shell
git clone https://github.com/prommis/flowsheet-inspector-lib.git
```

This creates a new folder named `flowsheet-inspector-lib` containing the
Flowsheet Inspector library and the PrOMMiS skills.

### 2. Open the repository folder

Move into the downloaded folder:

```{code} shell
cd flowsheet-inspector-lib
```

Run the remaining installation commands from this folder.

### 3. Add the repository as a Codex marketplace

Register the repository's plugin marketplace with Codex:

```{code} shell
codex plugin marketplace add .
```

The final period means "the current folder."

### 4. Install the plugin

Install the PrOMMiS skills from the marketplace:

```{code} shell
codex plugin add prommis-skills@prommis
```

### 5. Verify the installation

List the installed Codex plugins:

```{code} shell
codex plugin list
```

The output should include `prommis-skills` from the `prommis` marketplace.

### 6. Restart Codex

Close and reopen Codex, then start a new conversation. The skills are now
available in any workspace. Users can describe a task normally; they do not
need to name a skill.

## Included skills

The plugin includes these skills:

- `prommis-wrap` prepares a raw flowsheet for the Flowsheet Inspector.
- `prommis-change-value` finds and changes an approved `.fix()` value.
- `prommis-help-imports` finds exact import statements.
- `prommis-explain-diagnostics` investigates solver failures, infeasibility,
  IPOPT output, and IDAES diagnostics.

## Try the skills

Open the folder containing a flowsheet in Codex and try a request such as:

```{code} text
Wrap this raw PrOMMiS flowsheet for the Flowsheet Inspector.
```

Other examples include:

```{code} text
Change the fixed feed temperature to 350 K.
```

```{code} text
What is the correct import for FlowsheetRunner?
```

```{code} text
Explain why IPOPT failed on this flowsheet.
```

## Python environments

Installing the Codex plugin does not install PrOMMiS, IDAES, WaterTAP, Pyomo,
solvers, or Conda environments. Activate the environment required by the
flowsheet before asking Codex to run or inspect it.

Flowsheets that import from `prommis`, `idaes_fi`, or `idaes` generally use the
`idaes-fi` environment. Flowsheets that import from `idaes_examples` use the
`prommis-dev` environment.

## Update the installed skills

You do not need to reinstall the plugin when editing or running a flowsheet.
Follow these steps only when you want to download a newer version of the
PrOMMiS skills from GitHub.

Open a terminal in the cloned `flowsheet-inspector-lib` folder and download the
latest changes:

```{code} shell
git pull
```

Refresh the installed plugin:

```{code} shell
codex plugin add prommis-skills@prommis
```

Restart Codex and begin a new conversation so Codex loads the updated skills.

## Remove the skills

Remove the plugin with:

```{code} shell
codex plugin remove prommis-skills --marketplace prommis
```

To also remove the marketplace registration, run:

```{code} shell
codex plugin marketplace remove prommis
```

Deleting the cloned repository folder is optional after removing the plugin and
marketplace.

## Test the development branch

The PrOMMiS skills are currently being developed on the `prommis-skills`
branch. Until this work is merged into the official repository, testers should
use the following commands instead of the installation commands above.

Clone the development branch from the contributor repository:

```{code} shell
git clone --branch prommis-skills https://github.com/rhit-tanushree/flowsheet-inspector-lib.git
```

Open the downloaded repository:

```{code} shell
cd flowsheet-inspector-lib
```

Add it as a Codex marketplace and install the plugin:

```{code} shell
codex plugin marketplace add .
codex plugin add prommis-skills@prommis
```

Confirm that the plugin is installed:

```{code} shell
codex plugin list
```

Restart Codex and begin a new conversation before testing the skills.

This section is temporary and should be removed after `prommis-skills` is
merged into the official repository's `main` branch.

## Troubleshooting

Use the following commands to check the installation:

```{code} shell
codex plugin marketplace list
codex plugin list
```

If `prommis-skills` is installed but Codex does not use a skill, restart Codex
and begin a new conversation. If a skill reports missing Python imports or
executables, activate the Conda environment required by the flowsheet.

For general information about Codex plugins, see the
[OpenAI plugin documentation](https://developers.openai.com/plugins/build/plugins).

