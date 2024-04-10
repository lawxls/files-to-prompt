import os
import click
from fnmatch import fnmatch


def should_ignore(path, gitignore_rules, ignore_patterns):
    for rule in gitignore_rules:
        if fnmatch(os.path.basename(path), rule):
            return True
        if os.path.isdir(path) and fnmatch(os.path.basename(path) + "/", rule):
            return True
    for pattern in ignore_patterns:
        if os.path.isdir(path) and os.path.basename(path) == pattern:
            return True
        if fnmatch(path, pattern):
            return True
    return False


def read_gitignore(path):
    gitignore_path = os.path.join(path, ".gitignore")
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


def process_path(
    path, include_hidden, ignore_gitignore, gitignore_rules, ignore_patterns, output_file
):
    with open(output_file, "w") as output:
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    file_contents = f.read()
                output.write(f"{path}\n---\n{file_contents}\n\n---\n")
            except UnicodeDecodeError:
                warning_message = f"Warning: Skipping file {path} due to UnicodeDecodeError"
                click.echo(click.style(warning_message, fg="red"), err=True)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                    files = [f for f in files if not f.startswith(".")]

                if not ignore_gitignore:
                    gitignore_rules.extend(read_gitignore(root))

                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore(os.path.join(root, d), gitignore_rules, ignore_patterns)
                ]
                files = [
                    f
                    for f in files
                    if not should_ignore(os.path.join(root, f), gitignore_rules, ignore_patterns)
                ]

                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r") as f:
                            file_contents = f.read()

                        output.write(f"{file_path}\n---\n{file_contents}\n\n---\n")
                    except UnicodeDecodeError:
                        warning_message = f"Warning: Skipping file {file_path} due to UnicodeDecodeError"
                        click.echo(click.style(warning_message, fg="red"), err=True)


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--include-hidden",
    is_flag=True,
    help="Include files and folders starting with .",
)
@click.option(
    "--ignore-gitignore",
    is_flag=True,
    help="Ignore .gitignore files and include all files",
)
@click.option(
    "ignore_patterns",
    "--ignore",
    multiple=True,
    default=[],
    help="List of directory names to ignore, no matter where they are",
)
@click.option(
    "--output",
    default="output.txt",
    help="Output file to write the results to",
)
@click.version_option()
def cli(paths, include_hidden, ignore_gitignore, ignore_patterns, output):
    """
    Takes one or more paths to files or directories and outputs every file,
    recursively, each one preceded with its filename like this:

    path/to/file.py
    ----
    Contents of file.py goes here

    ---
    path/to/file2.py
    ---
    ...
    """
    gitignore_rules = []
    output_file = os.path.join(os.getcwd(), output)
    for path in paths:
        if not os.path.exists(path):
            raise click.BadArgumentUsage(f"Path does not exist: {path}")
        if not ignore_gitignore:
            gitignore_rules.extend(read_gitignore(os.path.dirname(path)))
        process_path(
            path, include_hidden, ignore_gitignore, gitignore_rules, ignore_patterns, output_file
        )
