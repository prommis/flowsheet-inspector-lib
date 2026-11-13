# Commands

## Console command-line interface 

The package provides the `ifi` command for console usage
(the mnemonic is **I**DAES **F**lowsheet **I**nspector).
Use `ifi --help` to see the top-level command list.

Global options:
```
--json/-J   Where appropriate, show JSON output instead 
            of plain text output. Useful for interfacing
            with scripts and other automated processes.
```

### Subcommands

* **ifi db migrate**: usage: IDAES Flowsheet Inspector db migrate [-h] [--file FILE]
    ```
    Migrate to latest database version
    --file, -f FILE  Database file (instead of default)
    ```
* **ifi db info**: usage: IDAES Flowsheet Inspector db info [-h] [--file FILE]
    ```
    Show current database information
    --file, -f FILE  Database file (instead of default)
    ```
* **ifi flowsheet run**: usage: IDAES Flowsheet Inspector flowsheet run [-h] [--file FILE]
    ```
    Run flowsheet
    --file, -f FILE       Flowsheet Python file
    --module, -m MODULE   Flowsheet Python module name
    --name, -n NAME       Flowsheet variable name
    --last-step, -l LAST_STEP
    Flowsheet step at which to stop the run
    --no-db               Do not use the report database
    ```
* **ifi flowsheet steps**: usage: IDAES Flowsheet Inspector flowsheet steps [-h] [--file FILE]
    ```
    Get defined steps for flowsheet(s)
    --file, -f FILE      Flowsheet Python file
    --module, -m MODULE  Flowsheet Python module name
    ```
    
## Programmatic usage

Each sub-command available through the `ifi` command can also be found in the `idaes_fi.commands` module, where the name of the function is simply the subcommand and sub-subcommand name separated by an underscore.
For example: `ifi db migrate` &rarr; <tt>idaes_fi.commands.db_migrate()</tt>.

## Python interpreter usage

Finally, to run the commands using the Python interpreter's `-c` option, which avoids having to invoke the `ifi` command through the shell, you can import the module and use the functions directly.

Note that formatting of the output is done by the CLI wrapper, so this may need to be recreated. For example, to print out DB info as JSON you can run: `python -c "import json; from idaes_fi.commands import *; print(json.dumps(db_info(), cls=PathJSONEncoder))"`. The PathJSONEncoder class is defined in the *commands* module in order to handle Python's *pathlib.Path* objects. 