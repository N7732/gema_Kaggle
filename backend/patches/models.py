from django.db import models
from issues.models import Issue

class Patch(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='patches')
    diff_content = models.TextField()
    turns_used = models.PositiveIntegerField(default=1)
    lines_changed = models.PositiveIntegerField(default=0)
    is_minimal = models.BooleanField(default=True)
    tests_passed = models.BooleanField(default=False)
    agent_mode = models.CharField(max_length=64, default='codeguardian_full')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Patch for {self.issue.task_id} (Passed: {self.tests_passed})"
