from cmd import Cmd
from todotxtlib import Task
from rich.table import Table
from prompt_toolkit import prompt
from pathlib import Path
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError


class PriorityValidator(Validator):
    """Validator to ensure priority is a single uppercase letter (A-Z) or empty."""

    def validate(self, document):
        text = document.text.strip()
        if text and (len(text) != 1 or not text.isalpha() or not text.isupper()):
            raise ValidationError(
                message="Priority must be a single uppercase letter (A-Z) or empty."
            )


class TaskShell(Cmd):
    intro = "Welcome to the Interactive Task Manager (todo.txt format)! Type ? or help to see commands."
    prompt = "(task-manager) "

    def __init__(self, tasks, td_manager, console):
        super().__init__()
        self.td = tasks
        self.td_manager = td_manager
        self.console = console

    def save_tasks(self):
        """Save the current tasks to the file."""
        self.td_manager.write_tasks(self.td)

    def do_add(self, arg):
        """Add a new task with an interactive form."""
        self.console.print("\n[bold cyan]Add a new task:[/bold cyan]")

        task_text = prompt("Task description: ").strip()
        if not task_text:
            self.console.print("[bold red]Task description cannot be empty![/bold red]")
            return

        priority = prompt(
            "Priority (A-Z, optional): ", validator=PriorityValidator(), default=""
        ).strip()

        # Fetch existing projects and contexts
        projects, contexts = self.extract_projects_and_contexts()

        # Set up auto-completion
        project_completer = WordCompleter(projects, ignore_case=True, sentence=True)
        context_completer = WordCompleter(contexts, ignore_case=True, sentence=True)

        def get_multiselect_input(description, completer):
            """Get multiple selections from the user with autocomplete."""
            selections = []
            prompt_input = prompt(
                description, completer=completer, complete_while_typing=True
            ).strip()
            while prompt_input:
                if prompt_input.startswith("+"):
                    selections.extend(
                        [
                            proj.strip("+").strip()
                            for proj in prompt_input.lstrip("+").split("+")
                        ]
                    )
                elif prompt_input.startswith("@"):
                    selections.extend(
                        [
                            cont.strip("@").strip()
                            for cont in prompt_input.lstrip("@").split("@")
                        ]
                    )
                prompt_input = prompt(
                    description, completer=completer, complete_while_typing=True
                ).strip()
            return selections

        projects = get_multiselect_input(
            "Projects (e.g., +Work +Home, optional): ", project_completer
        )
        contexts = get_multiselect_input(
            "Contexts (e.g., @Home @Work, optional): ", context_completer
        )
        task_string = task_text
        # Create a Task object and add it
        task = Task(
            task_string, priority=priority, projects=projects, contexts=contexts
        )
        self.td.append(task)
        self.save_tasks()
        self.console.print(f"[green]Task added:[/green] {task_string}")

    def do_list(self, arg):
        """List all tasks with projects, contexts, and tags."""
        if not self.td:
            self.console.print("[yellow]No tasks available![/yellow]")
            return

        table = Table(title="Task List")
        table.add_column("ID", style="cyan")
        table.add_column("Task", style="magenta")
        table.add_column("Priority", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Created", style="blue")
        table.add_column("Completed", style="red")
        table.add_column("Projects", style="bold blue")
        table.add_column("Contexts", style="bold green")

        for idx, task in enumerate(self.td, 1):
            status = "[green]✔ Completed" if task.completed else "[red]✖ Pending"
            priority = task.priority if task.priority else "-"
            task_text = task.description
            projects = (
                ", ".join(f"+{proj}" for proj in task.projects)
                if task.projects
                else "-"
            )
            contexts = (
                ", ".join(f"@{cont}" for cont in task.contexts)
                if task.contexts
                else "-"
            )
            created = task.created_date if task.created_date else "-"
            due = task.completed_date if task.completed_date else "-"
            table.add_row(
                str(idx), task_text, priority, status, created, due, projects, contexts
            )

        self.console.print(table)

    def do_complete(self, arg):
        """Mark a task as completed: complete <task ID>"""
        try:
            task_id = int(arg) - 1
            if 0 <= task_id < len(self.td):
                self.td[task_id].mark_completed()
                self.save_tasks()
                self.console.print(
                    f"[bold green]Task {task_id + 1} marked as completed![/bold green]"
                )
            else:
                self.console.print("[red]Invalid task ID![/red]")
        except ValueError:
            self.console.print("[bold red]Please enter a valid task ID.[/bold red]")

    def do_remove(self, arg):
        """Remove a task: remove <task ID>"""
        try:
            task_id = int(arg) - 1
            if 0 <= task_id < len(self.td):
                removed_task = self.td.pop(task_id)
                self.save_tasks()
                self.console.print(
                    f"[bold yellow]Task removed:[/bold yellow] {removed_task.description}"
                )
            else:
                self.console.print("[red]Invalid task ID![/red]")
        except ValueError:
            self.console.print("[bold red]Please enter a valid task ID.[/bold red]")

    def do_switch(self, arg):
        """Switch to a different todo file using a file selector."""
        global td_manager, td
        selected_file = self.select_file()
        if not selected_file:
            self.console.print(
                "[bold yellow]No file selected. Operation cancelled.[/bold yellow]"
            )
            return
        td_manager = self.td_manager.__class__(selected_file)
        td = td_manager.read_tasks()
        self.console.print(
            f"[bold green]Switched to file: {selected_file}[/bold green]"
        )

    def do_exit(self, arg):
        """Exit the Task Manager."""
        self.console.print("[bold cyan]Goodbye![/bold cyan]")
        return True

    def default(self, line):
        self.console.print(f"[red]Unknown command:[/red] {line}")

    def extract_projects_and_contexts(self):
        """Extract all unique projects (+Project) and contexts (@Context) from tasks."""
        projects = set()
        contexts = set()
        for task in self.td:
            for tag in task.projects:
                projects.add(f"+{tag}")
            for context in task.contexts:
                contexts.add(f"@{context}")
        return sorted(projects), sorted(contexts)

    def select_file(self):
        """Text-based file selector to choose a todo.txt file with an option to create a new file."""
        todo_files = [f.name for f in Path().glob("*.txt") if f.name.endswith(".txt")]
        self.console.print("[bold cyan]Select a todo.txt file:[/bold cyan]")
        for i, file in enumerate(todo_files, 1):
            self.console.print(f"{i}. {file}")
        self.console.print(f"{len(todo_files) + 1}. Create a new .txt file")

        try:
            choice = int(
                prompt(
                    "Enter the number of the file to switch to or create a new file: "
                ).strip()
            )
            if 1 <= choice <= len(todo_files):
                return todo_files[choice - 1]
            elif choice == len(todo_files) + 1:
                new_file_name = prompt("Enter the name for the new .txt file: ").strip()
                if not new_file_name.endswith(".txt"):
                    new_file_name += ".txt"
                with open(new_file_name, "w") as f:
                    self.console.print(
                        f"[bold green]File '{new_file_name}' created.[/bold green]"
                    )
                return new_file_name
            else:
                self.console.print("[red]Invalid selection![/red]")
                return None
        except ValueError:
            self.console.print("[bold red]Please enter a valid number.[/bold red]")
            return None
