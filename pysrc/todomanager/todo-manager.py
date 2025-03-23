#!/usr/bin/env python3

import cmd
import os
from todotxtlib import TodoTxtFileManager, Task
from rich.console import Console
from rich.table import Table
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from pathlib import Path

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

def extract_projects_and_contexts():
    """Extract all unique projects (+Project) and contexts (@Context) from tasks."""
    projects = set()
    contexts = set()
    for task in td:
        for tag in task.projects:
            projects.add(f"+{tag}")
        for context in task.contexts:
            contexts.add(f"@{context}")
    return sorted(projects), sorted(contexts)

class PriorityValidator(Validator):
    """Validator to ensure priority is a single uppercase letter (A-Z) or empty."""
    def validate(self, document):
        text = document.text.strip()
        if text and (len(text) != 1 or not text.isalpha() or not text.isupper()):
            raise ValidationError(message="Priority must be a single uppercase letter (A-Z) or empty.")

def select_file():
    """Text-based file selector to choose a todo.txt file with an option to create a new file."""
    todo_files = [f.name for f in Path().glob("*.txt") if f.name.endswith(".txt")]
    console.print("[bold cyan]Select a todo.txt file:[/bold cyan]")
    for i, file in enumerate(todo_files, 1):
        console.print(f"{i}. {file}")
    console.print(f"{len(todo_files) + 1}. Create a new .txt file")

    try:
        choice = int(prompt("Enter the number of the file to switch to or create a new file: ").strip())
        if 1 <= choice <= len(todo_files):
            return todo_files[choice - 1]
        elif choice == len(todo_files) + 1:
            new_file_name = prompt("Enter the name for the new .txt file: ").strip()
            if not new_file_name.endswith(".txt"):
                new_file_name += ".txt"
            with open(new_file_name, 'w') as f:
                console.print(f"[bold green]File '{new_file_name}' created.[/bold green]")
            return new_file_name
        else:
            console.print("[red]Invalid selection![/red]")
            return None
    except ValueError:
        console.print("[bold red]Please enter a valid number.[/bold red]")
        return None

class TaskShell(cmd.Cmd):
    intro = "Welcome to the Interactive Task Manager (todo.txt format)! Type ? or help to see commands."
    prompt = "(task-manager) "

    def do_add(self, arg):
        """Add a new task with an interactive form."""
        console.print("\n[bold cyan]Add a new task:[/bold cyan]")

        task_text = prompt("Task description: ").strip()
        if not task_text:
            console.print("[bold red]Task description cannot be empty![/bold red]")
            return

        priority = prompt("Priority (A-Z, optional): ", validator=PriorityValidator(), default="").strip()

        # Fetch existing projects and contexts
        projects, contexts = extract_projects_and_contexts()

        # Set up auto-completion
        project_completer = WordCompleter(projects, ignore_case=True, sentence=True)
        context_completer = WordCompleter(contexts, ignore_case=True, sentence=True)

        def get_multiselect_input(description, completer):
            """Get multiple selections from the user with autocomplete."""
            selections = []
            prompt_input = prompt(description, completer=completer, complete_while_typing=True).strip()
            while prompt_input:
                if prompt_input.startswith("+"):
                    selections.extend([proj.strip("+").strip() for proj in prompt_input.lstrip("+").split("+")])
                elif prompt_input.startswith("@"):
                    selections.extend([cont.strip("@").strip() for cont in prompt_input.lstrip("@").split("@")])
                prompt_input = prompt(description, completer=completer, complete_while_typing=True).strip()
            return selections

        projects = get_multiselect_input("Projects (e.g., +Work +Home, optional): ", project_completer)
        contexts = get_multiselect_input("Contexts (e.g., @Home @Work, optional): ", context_completer)
        task_string = task_text
        # Create a Task object and add it
        task = Task(task_string, priority=priority, projects=projects, contexts=contexts)
        td.append(task)
        save_tasks()
        console.print(f"[green]Task added:[/green] {task_string}")

    def do_list(self, arg):
        """List all tasks."""
        if not td:
            console.print("[yellow]No tasks available![/yellow]")
            return

        table = Table(title="Task List")
        table.add_column("ID", style="cyan")
        table.add_column("Task", style="magenta")
        table.add_column("Priority", style="yellow")
        table.add_column("Status", style="green")

        for idx, task in enumerate(td, 1):
            status = "[green]✔ Completed" if task.completed else "[red]✖ Pending"
            priority = task.priority if task.priority else "-"
            task_text = task.description
            table.add_row(str(idx), task_text, priority, status)

        console.print(table)

    def do_complete(self, arg):
        """Mark a task as completed: complete <task ID>"""
        try:
            task_id = int(arg) - 1
            if 0 <= task_id < len(td):
                td[task_id].mark_completed()
                save_tasks()
                console.print(f"[bold green]Task {task_id + 1} marked as completed![/bold green]")
            else:
                console.print("[red]Invalid task ID![/red]")
        except ValueError:
            console.print("[bold red]Please enter a valid task ID.[/bold red]")

    def do_remove(self, arg):
        """Remove a task: remove <task ID>"""
        try:
            task_id = int(arg) - 1
            if 0 <= task_id < len(td):
                removed_task = td.pop(task_id)
                save_tasks()
                console.print(f"[bold yellow]Task removed:[/bold yellow] {removed_task.description}")
            else:
                console.print("[red]Invalid task ID![/red]")
        except ValueError:
            console.print("[bold red]Please enter a valid task ID.[/bold red]")

    def do_switch(self, arg):
        """Switch to a different todo file using a file selector."""
        global td_manager, td
        selected_file = select_file()
        if not selected_file:
            console.print("[bold yellow]No file selected. Operation cancelled.[/bold yellow]")
            return
        td_manager = TodoTxtFileManager(selected_file)
        td = td_manager.read_tasks()
        console.print(f"[bold green]Switched to file: {selected_file}[/bold green]")

    def do_exit(self, arg):
        """Exit the Task Manager."""
        console.print("[bold cyan]Goodbye![/bold cyan]")
        return True

    def default(self, line):
        console.print(f"[red]Unknown command:[/red] {line}")

if __name__ == "__main__":
    shell = TaskShell()

    while True:
        try:
            user_input = prompt("(task-manager) ", completer=WordCompleter(["add", "list", "complete", "remove", "switch", "exit"], ignore_case=True))
            shell.onecmd(user_input)
            if user_input == "exit":
                break
        except KeyboardInterrupt:
            console.print("\n[bold cyan]Exiting Task Manager. Goodbye![/bold cyan]")
            break