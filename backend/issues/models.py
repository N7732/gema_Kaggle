from django.db import models

class Issue(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('failed', 'Failed'),
    ]

    task_id = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=255)
    problem_statement = models.TextField()
    repo_name = models.CharField(max_length=255, default='local')
    target_file = models.CharField(max_length=255, blank=True, null=True)
    target_symbol = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_id}: {self.title}"
