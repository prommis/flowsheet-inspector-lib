---
title: Flowsheet Inspector Library Usage
---
## Flowsheet Inspector Library Usage

The Flowsheet Inspector (FI) library is primarily a way to "wrap" the functions
used to build, set up, and solve a flowsheet so that these steps can be
controlled from outside the program, and also arbitrary "actions" can run before
and after each step or each sequence of steps. Built-in actions include
gathering information on variable state, creating a diagram, and running the
diagnostics, but this is extensible.

This section starts from the assumption that you have a FI-wrapped flowsheet and
describes how to run it and get back the information it collects during the
actions. For information on how to wrap the flowsheet, see the [API](api)
section.

### VSCode extension

You can load and run FI flowsheets with our VSCode extension. Please see the
[FI VSCode extension](https://github.com/prommis/flowsheet-inspector) for
details.

### Command-line (shell)



### Python API in a script
 
 
### Python API in a Jupyter Notebook