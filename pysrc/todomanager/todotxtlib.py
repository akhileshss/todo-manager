import re
from datetime import datetime

class Task:
    def __init__(self, description, completed=False, priority=None, created_date=None, completed_date=None, tags=None, contexts=None):
        self.description = description
        self.completed = completed
        self.priority = priority
        self.created_date = created_date or datetime.now().strftime('%Y-%m-%d')
        self.completed_date = completed_date
        self.tags = tags or []
        self.contexts = contexts or []

    def __str__(self):
        return self.to_string()

    def to_string(self):
        task_str = ''
        if self.completed:
            task_str += 'x '
            task_str += self.completed_date + ' ' if self.completed_date else ''
        if self.priority:
            task_str += '(' + self.priority + ') '
        task_str += self.created_date + ' '
        task_str += self.description + ' '
        contexts_str = ' '.join(['@' + context for context in self.contexts])
        task_str += contexts_str + ' ' if contexts_str else ''
        tags_str = ' '.join(['+' + tag for tag in self.tags])
        task_str += tags_str + ' ' if tags_str else ''
        return task_str.strip()

    def mark_completed(self):
        self.completed = True
        self.completed_date = datetime.now().strftime('%Y-%m-%d')

    def add_context(self, context):
        if context not in self.contexts:
            self.contexts.append(context)

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)


class TodoTxtFileManager:
    DATE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2})')
    TASK_PATTERN = re.compile(r'^(?P<completed>x\s*)?(?P<completed_date>\d{4}-\d{2}-\d{2})?\s*(?P<priority>\([A-Za-z]\))?\s*(?P<created_date>\d{4}-\d{2}-\d{2})?\s*(?P<description>.+)$')

    def __init__(self, file_path):
        self.file_path = file_path

    def read_tasks(self):
        tasks = []
        with open(self.file_path, 'r') as file:
            for line in file:
                task_line = line.strip()
                if task_line:
                    task = self._parse_task_line(task_line)
                    tasks.append(task)
        return tasks

    def write_tasks(self, tasks):
        with open(self.file_path, 'w') as file:
            for task in tasks:
                file.write(task.to_string() + '\n')

    def _parse_task_line(self, task_line):
        match = self.TASK_PATTERN.match(task_line)
        if not match:
            raise ValueError(f"Invalid task line format: {task_line}")

        completed = bool(match.group('completed'))
        completed_date = match.group('completed_date')
        priority = match.group('priority')[1] if match.group('priority') else None
        created_date = match.group('created_date')
        description = match.group('description')

        contexts = re.findall(r'\s+@(\w+)', description)
        tags = re.findall(r'\s+\+(\w+)', description)

        description = re.sub(r'\s*[@+]\w+', '', description).strip()

        return Task(description, completed, priority, created_date, completed_date, tags, contexts)