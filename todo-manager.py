#!/usr/bin/env python3

from todotxtlib import TodoTxtFileManager
from rich.console import Console
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt
from task_shell import TaskShell

# Constants
TODO_FILE = "todo.txt"

# Rich console for better UI
console = Console()

# Initialize TodoTxtFileManager object
td_manager = TodoTxtFileManager(TODO_FILE)
td = td_manager.read_tasks()


def save_tasks():
    """Save the current tasks to the file."""
    td_manager.write_tasks(td)


if __name__ == "__main__":
    shell = TaskShell(td, td_manager, console)

    while True:
        try:
            user_input = prompt(
                "(task-manager) ",
                completer=WordCompleter(
                    ["add", "list", "complete", "remove", "switch", "exit"],
                    ignore_case=True,
                ),
            )
            shell.onecmd(user_input)
            if user_input == "exit":
                break
        except KeyboardInterrupt:
            console.print("\n[bold cyan]Exiting Task Manager. Goodbye![/bold cyan]")
            break
