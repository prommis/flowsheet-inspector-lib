---
name: prommis-help-imports
description: Returns the exact import statement for any PrOMMiS, IDAES, Pyomo, or Flowsheet Inspector module. TRIGGER when: user gets ImportError or ModuleNotFoundError, doesn't know import path, asks how to import LeachingTrain, FlowsheetRunner, DiagnosticsToolbox, Flash, Mixer, or any unit model or property package, asks where a class lives. DO NOT TRIGGER when: user wants to wrap a flowsheet, change a value, or debug a solver error.
compatibility: Requires the same conda environment as the flowsheet being worked on — idaes-fi for flowsheets importing from prommis or idaes_fi, prommis-dev for flowsheets importing from idaes_examples.
metadata:
  author: Tanushree Subramanian
  version: "1.0"
---

# PrOMMiS Help With Imports

Finding the right import path in PrOMMiS, IDAES, or Pyomo requires
knowing exactly where each class lives in the codebase. Import paths
can change between versions so this skill searches the user's locally
installed packages by running a script directly — no hardcoded lookup
tables, no user involvement in the search process.

## When to Use

Use this when:
- you get an ImportError or ModuleNotFoundError
- you don't know the correct import path for a class
- you want to import a unit model, property package, or utility
- you're not sure which package a class lives in

## Core Concepts

**Import statement** — the full line of Python code needed to bring
a class into your file:
```python
from prommis.leaching.leach_train import LeachingTrain
```

**Module path** — the exact location of a class in the codebase,
e.g. `prommis.leaching.leach_train` tells Python to look in the
`leaching` folder for the `leach_train.py` file.

**Duplicate class names** — some class names exist in multiple
modules. When this happens the skill gathers context from the user
to determine which one is correct.

## Note on Import Paths

Import paths are not hardcoded in this skill — they are found by
running `scripts/get_imports.py` directly against the locally
installed packages. This means the results always reflect the
user's actual installed version.

Resolve `scripts/get_imports.py` relative to the directory that
contains this `SKILL.md`. From the repository root, that path is
`skills/prommis-help-imports/scripts/get_imports.py`.

## Stage 1 — Gather Context

Always announce: "Stage 1 — finding import for [class name]."

Before running the search script, ask the user one question:
"Do you have more context about how you're using this class?
e.g. a file you're working on, a process you're building, or
an error message you got"

Wait for the user's response. Three possible cases:

**Case 1 — user names a specific file:**
Read that file directly from the workspace silently. Check the
existing imports at the top of the file to determine which conda
environment is needed:
- imports from idaes_examples → prommis-dev
- imports from prommis or idaes_fi → idaes-fi
Store the existing imports — they will be used to resolve
duplicates in stage 2 and to find the correct insertion point
in stage 3.

**Case 2 — user gives other context:**
Note the context. Use it to resolve duplicates in stage 2 if
multiple matches are found. Try both conda environments in stage 2.

**Case 3 — user has no context:**
Proceed without context. Try both conda environments in stage 2.
If multiple matches are found, ask targeted questions to resolve.

## Stage 2 — Search and Resolve

Always announce: "Stage 2 — searching installed packages."

Run the script silently — do not show the user any script output,
warnings, or errors. Only surface the final matched import paths.

**If a file was named in stage 1:**
Run the script in the environment determined from the file's imports:
```bash
conda run -n [environment] python <path-to-this-skill>/scripts/get_imports.py <class_name>
```

**If no file was named:**
Run the script in both environments:
```bash
conda run -n idaes-fi python <path-to-this-skill>/scripts/get_imports.py <class_name>
conda run -n prommis-dev python <path-to-this-skill>/scripts/get_imports.py <class_name>
```

Combine all unique matches from both runs.

**If 1 unique match found:**
Go directly to stage 3.

**If multiple unique matches found:**
Work through this resolution process in order:

Resolution step 1 — check file imports:
If a file was named, check its existing imports. If any existing
import is from the same top-level module folder as one of the
matches, return that match.

Example: file has
`from prommis.precipitate.precipitate_liquid_properties import AqueousParameter`
and matches include `prommis.precipitate.precipitator` and
`prommis.cmi_precipitator.opt_based_precipitator` — return
`prommis.precipitate.precipitator` because the file already
imports from `prommis.precipitate`.

If resolved, go to stage 3.

Resolution step 2 — use context provided in stage 1:
If the user gave context like a process description or error
message, use it to select the most likely match.
If resolved, go to stage 3.

Resolution step 3 — ask targeted questions:
If still unresolved, ask the specific question for this class:

Precipitator:
"Which folder in the PrOMMiS repo does your flowsheet live in
or reference? e.g. precipitate, cmi_precipitator, or nanofiltration"

AqueousParameter:
"Is your code in the precipitate folder or the cmi_precipitator
folder?"

CoalRefuseParameters:
"Are you working with leaching or crushing/solid handling?"

QGESSCosting:
"Is this for a PrOMMiS rare earth plant, or an IDAES power
generation plant?"

REEFeedRoaster:
"Is your flowsheet dynamic (changes over time) or steady-state
(fixed snapshot)?"

For any other duplicate not listed above:
"Which of these module paths looks most familiar based on your
other imports?
1. [import path 1]
2. [import path 2]"

Resolution step 4 — last resort:
If still unresolved after targeted questions, list all matches
and point to the source:
"I found [X] classes with this name:
1. [import path 1]
2. [import path 2]
Check the PrOMMiS GitHub to identify which one matches:
https://github.com/prommis/prommis/tree/main/src/prommis"

**If no match found in either environment:**
Tell the user:
"No match found for [class name] in either environment.
Most likely causes:
- class name is misspelled — class names are case sensitive
- class was added or renamed in a newer version
Please check the exact spelling and try again."

## Stage 3 — Confirm and Insert

Always announce: "Stage 3 — adding import to file."

**If the user named a file:**

First check silently whether this import already exists in the
file. If it does, tell the user:
"This import is already in your file — no changes needed."

If it does not exist yet, run the verification command silently:
```bash
conda run -n [environment] python -c "from [module_path] import [class_name]; print('import works')"
```

If verification passes, find the correct location to insert the
import in the file using this logic:

1. If other imports from the same top-level package already exist
   in the file, insert the new import next to them.
   e.g. if adding `from pyomo.network import Arc` and the file
   already has `from pyomo.network import Port`, insert Arc
   on the line immediately after Port.

2. If imports from the same top-level package exist but in a
   different submodule, insert after the last import from that
   top-level package.
   e.g. if adding `from idaes.core import FlowsheetBlock` and
   the file has a block of `from idaes.models...` imports,
   insert after the last idaes import.

3. If no imports from the same package exist at all, insert
   after the last import block at the top of the file.

Write the import directly to the file at the determined location.
Do not show the user the import as a code block to copy — confirm:
"Done. Added [import statement] to [filename] after [neighboring
import line]."

If verification fails, try the other conda environment silently
and run again. If both fail tell the user:
"Verification failed in both environments. The package installation
may be incomplete. Try reinstalling with:
conda activate [environment]
pip install -e . in the prommis or idaes repo directory"

**If no file was named:**
Show the confirmed import in a code block and tell the user
where to add it:
```python
from [module_path] import [class_name]
```
"Add this at the top of your file with your other imports,
grouped with other [package name] imports if any exist."

After confirming, suggest related skills:
- if they are building a new flowsheet: suggest prommis-wrap
- if they are getting solver errors: suggest prommis-explain-diagnostics

## Output Rules

Never show the user:
- internal terminal commands being run
- conda environment switching reasoning
- script execution details or errors
- file reading operations
- intermediate steps or fallback logic
- any reasoning about which environment or approach to use
- the verification command or its raw output

Only show the user:
- the stage announcements
- any questions needed to resolve ambiguity
- the one line confirmation after writing to the file
- a one line verification result if applicable
- next step suggestions

Keep all internal reasoning, script execution, environment
detection, and file operations invisible to the user. The user
should only see clean stage-by-stage output.

## Rules

- never hardcode import paths — always run scripts/get_imports.py
- always ask about file context before running the search
- if a file is named, read it directly to determine the environment
- never guess when there are multiple matches — always work through
  the resolution process
- never add an import that already exists in the user's file
- always run the verification command silently in stage 3
- always try both environments before reporting no match
- never show the user internal script output, warnings, or errors
- if a file is named always write the import directly to the file
  at the correct location — never ask the user to copy and paste
- if no file is named show the import as a code block for the
  user to add manually

## DO NOT Rules

- do not return an import path from memory — always run the script
- do not ask the user to run any terminal commands themselves
- do not show the user any script output, warnings, or errors
- do not guess which module is correct for duplicate class names
  without working through the resolution process
- do not add an import that already exists in the file
- do not return paths not confirmed by the script output
- do not skip the verification step in stage 3
- do not show the user the verification command or its raw output
- do not ask the user to copy and paste if a file was named —
  write it directly

## Common Pitfalls

- wrong environment: if no file is named, always try both
  environments — a class may only be installed in one
- duplicate class names: always work through the resolution process,
  never guess
- misspelled class names: class names are case sensitive — if no
  match is found, ask the user to double check the exact spelling
- import already exists: always check the user's file before
  writing to avoid adding a duplicate
- showing internal steps: never show the user terminal commands,
  script output, or environment switching — keep it clean
- wrong insertion point: always group new imports with existing
  imports from the same package — never add at a random location

## Deviation Handling

If the user gives an informal class name like "the leaching train":
infer the most likely class name, confirm with the user:
"I think you mean LeachingTrain — is that right?"
Then proceed with stage 1.

If the user wants multiple imports at once:
handle one at a time — full search, verification, and insertion
for each class before moving to the next.

If conda is not available:
tell the user:
"conda does not appear to be accessible. Make sure Miniconda or
Anaconda is installed and conda is in your PATH."

If the script file is not found:
tell the user:
"The search script was not found at
<path-to-this-skill>/scripts/get_imports.py.
Resolve <path-to-this-skill> from the directory that contains this
SKILL.md."

## Example Conversations

**Example 1 — single match, file named, import written directly:**

User: "how do I import LeachingTrain in my_flowsheet.py"

AI: "Stage 1 — finding import for LeachingTrain.
Do you have more context about how you're using this class?
e.g. a file you're working on, a process you're building, or
an error message you got"

User: "yes I'm working on my_flowsheet.py"

AI: "Stage 2 — searching installed packages.

Stage 3 — adding import to file.
Done. Added from prommis.leaching.leach_train import LeachingTrain
to my_flowsheet.py after the last prommis import."

---

**Example 2 — duplicate match, no file, targeted question:**

User: "how do I import Precipitator"

AI: "Stage 1 — finding import for Precipitator.
Do you have more context about how you're using this class?
e.g. a file you're working on, a process you're building, or
an error message you got"

User: "no not really"

AI: "Stage 2 — searching installed packages.
I found 3 classes called Precipitator in different modules.
Which folder in the PrOMMiS repo does your flowsheet live in
or reference? e.g. precipitate, cmi_precipitator, or nanofiltration"

User: "precipitate"

AI: "Stage 3 — adding import to file.
No file was named so here is the import to add manually:
```python
from prommis.precipitate.precipitator import Precipitator
```
Add this at the top of your file grouped with other
prommis.precipitate imports if any exist."

---

**Example 3 — import already exists:**

User: "how do I import FlowsheetBlock in my_flowsheet.py"

AI: "Stage 1 — finding import for FlowsheetBlock.
Do you have more context about how you're using this class?
e.g. a file you're working on, a process you're building, or
an error message you got"

User: "yes my_flowsheet.py"

AI: "Stage 2 — searching installed packages.

Stage 3 — adding import to file.
This import is already in your file — no changes needed."
