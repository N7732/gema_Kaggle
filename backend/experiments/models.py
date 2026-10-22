from django.db import models

class Experiment(models.Model):
    name = models.CharField(max_length=255)
    variant = models.CharField(max_length=64)
    total_tasks = models.PositiveIntegerField(default=0)
    resolved_tasks = models.PositiveIntegerField(default=0)
    pass_rate = models.FloatField(default=0.0)
    avg_turns = models.FloatField(default=1.0)
    avg_lines_changed = models.FloatField(default=0.0)
    avg_runtime_sec = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.variant}): {self.pass_rate}%"
