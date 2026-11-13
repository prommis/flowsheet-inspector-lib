"""
Automate useful outputs for documentation.
"""

import argparse
import re
from subprocess import check_output

CMD = "ifi"


def get_help(cmd=[], hmap=None):
    # run cmd with --help option and get output
    args = [CMD] + cmd + ["--help"]
    output = check_output(args)
    lines = [s.strip().decode("utf-8") for s in output.splitlines()]
    lines = [s for s in lines if len(s) > 1 and not s.startswith("-h")]
    if not lines:
        print
        return
    # look for list of subcommands
    flag, next_level = False, []
    for line in lines:
        if flag:
            m = re.search(r"\{(.*)\}", line)
            next_level = m.group(1).split(",")
            break
        elif line.strip() == "positional arguments:":
            flag = True
    # if subcommands are found, recurse
    if next_level:
        for name in next_level:
            get_help(cmd + [name], hmap=hmap)
    # otherwise get help for this leaf command
    else:
        flag = False
        help_lines = []
        for line in lines:
            # add option line
            if flag:
                help_lines.append(line)
            # set flag once options are found
            elif line.startswith("options:"):
                flag = True
            # extract description
            elif line and not re.match(r"^(b|\[)", line):
                help_lines.append(line)
        if help_lines and cmd:
            # add lines into hmap 'tree'
            # (and stop recursion)
            cur = hmap
            for tok in cmd[:-1]:
                if not tok in cur:
                    cur[tok] = {}
                cur = cur[tok]
            cur[cmd[-1]] = help_lines


def print_help(val, path):
    if isinstance(val, dict):
        for k, v in val.items():
            print_help(v, path + [k])
    else:
        label = " ".join(path)
        desc = val[0]
        print(f"* **{label}**: {desc}")
        indent = "    "
        print(f"{indent}```")
        for line in val[1:]:
            print(f"{indent}{line}")
        print(f"{indent}```")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["help"])
    args = p.parse_args()
    if args.mode == "help":
        hmap = {}
        get_help(hmap=hmap)
        print_help(hmap, ["ifi"])
