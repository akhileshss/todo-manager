#!/usr/bin/env python3

import cmd
import os
from pytodotxt import TodoTxt
from rich.console import Console
from rich.table import Table
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

# Constants
TODO_FILE = "todo.txt"

# Rich console for better UI
console = Console()

# Autocomplete for commands
task_completer = WordCompleter(
    ["add", "list", "complete", "remove", "exit"], ignore_case=True
)

# Initialize TodoTxt object
td = TodoTxt(TODO_FILE)
if os.path.exists(TODO_FILE):
    td.parse()

def save_tasks():
    """Save the current tasks to the file."""
    td.save()

def sort_tasks(tasks, sort_by):
    """Sort tasks based on the given column."""
    if sort_by == "priority":
        return sorted(tasks, key=lambda t: t.priority if t.priority else "Z")
    elif sort_by == "status":
        return sorted(tasks, key=lambda t: t.is_completed)  # Pending first
    elif sort_by == "task":
        return sorted(tasks, key=lambda t: t.text.lower())
    return tasks  # Default order

def filter_tasks(tasks, filter_by):
    """Filter tasks by pending or completed status."""
    if filter_by == "pending":
        return [task for task in tasks if not task.is_completed]
    elif filter_by == "completed":
        return [task for task in tasks if task.is_completed]
    return tasks  # No filter applied

class TaskShell(cmd.Cmd):
    intro = "Welcome to the Interactive Task Manager (todo.txt format)! Type ? or help to see commands."
    prompt = "(task-manager) "

    def do_add(self, arg):
        """Add a new task: add <task description>"""
        if not arg:
            console.print("[bold red]Task description cannot be empty![/bold red]")
            return
        td.add(arg)
        save_tasks()
        console.print(f"[green]Task added:[/green] {arg}")

    def do_list(self, arg):
        """List all tasks with optional sorting and filtering.
        
        Usage:
            list --sort=priority|status|task --filter=pending|completed
        """
        if not td.tasks:
            console.print("[yellow]No tasks available![/yellow]")
            return

        # Extract sorting and filtering arguments if provided
        sort_by, filter_by = None, None
        args = arg.split()
        for a in args:
            if a.startswith("--sort="):
                sort_by = a.split("=")[1].strip()
            elif a.startswith("--filter="):
                filter_by = a.split("=")[1].strip()

        tasks = td.tasks
        tasks = filter_tasks(tasks, filter_by)
        tasks = sort_tasks(tasks, sort_by)

        table = Table(title=f"Task List (Sorted: {sort_by if sort_by else 'Default'}, Filtered: {filter_by if filter_by else 'None'})")
        table.add_column("ID", style="cyan")
        table.add_column("Task", style="magenta")
        table.add_column("Priority", style="yellow")
        table.add_column("Status", style="green")

        for idx, task in enumerate(tasks, 1):
            status = "[green]✔ Completed" if task.is_completed else "[red]✖ Pending"
            priority = task.priority if task.priority else "-"
            table.add_row(str(idx), task.text, priority, status)

        console.print(table)

    def do_complete(self, arg):
        """Mark a task as completed: complete <task ID>"""
        try:
            task_id = int(arg) - 1
            if 0 <= task_id < len(td.tasks):
                td.tasks[task_id].complete()
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
            if 0 <= task_id < len(td.tasks):
                removed_task = td.tasks.pop(task_id)
                save_tasks()
                console.print(f"[bold yellow]Task removed:[/bold yellow] {removed_task.text}")
            else:
                console.print("[red]Invalid task ID![/red]")
        except ValueError:
            console.print("[bold red]Please enter a valid task ID.[/bold red]")

    def do_exit(self, arg):
        """Exit the Task Manager"""
        console.print("[bold cyan]Goodbye![/bold cyan]")
        return True

    def default(self, line):
        console.print(f"[red]Unknown command:[/red] {line}")

if __name__ == "__main__":
    shell = TaskShell()
    
    while True:
        try:
            user_input = prompt("(task-manager) ", completer=task_completer)
            shell.onecmd(user_input)
            if user_input == "exit":
                break
        except KeyboardInterrupt:
            console.print("\n[bold cyan]Exiting Task Manager. Goodbye![/bold cyan]")
            break

