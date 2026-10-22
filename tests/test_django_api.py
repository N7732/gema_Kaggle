"""
Integration and API tests for CodeGuardian Django Backend.
"""

import os
import pytest
from rest_framework.test import APIClient

# Configure Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

@pytest.fixture
def api_client():
    import django
    django.setup()
    return APIClient()

@pytest.mark.django_db
def test_issue_lifecycle_api(api_client):
    from issues.models import Issue

    # 1. Create Issue
    res = api_client.post('/api/issues/', {
        'task_id': 'kaggle_task_42',
        'title': 'Test Issue for Gemma Agent',
        'problem_statement': 'Fix index error in tokenizer',
        'repo_name': 'transformers_mini',
        'status': 'open'
    }, format='json')
    assert res.status_code == 201
    issue_id = res.data['id']

    # 2. List Issues
    list_res = api_client.get('/api/issues/')
    assert list_res.status_code == 200
    assert list_res.data['count'] == 1

    # 3. Create Patch associated with Issue
    patch_res = api_client.post('/api/patches/', {
        'issue': issue_id,
        'diff_content': '--- a/tok.py\n+++ b/tok.py\n@@ -1 +1 @@\n-old\n+new',
        'turns_used': 2,
        'lines_changed': 2,
        'is_minimal': True,
        'tests_passed': True,
        'agent_mode': 'codeguardian_full'
    }, format='json')
    assert patch_res.status_code == 201

@pytest.mark.django_db
def test_experiment_api(api_client):
    res = api_client.post('/api/experiments/', {
        'name': 'Gemma 4 Ablation Run',
        'variant': 'codeguardian_full',
        'total_tasks': 4,
        'resolved_tasks': 4,
        'pass_rate': 100.0,
        'avg_turns': 1.75,
        'avg_lines_changed': 2.25,
        'avg_runtime_sec': 3.6
    }, format='json')
    assert res.status_code == 201
    assert res.data['pass_rate'] == 100.0

@pytest.mark.django_db
def test_openapi_schema_generation(api_client):
    res = api_client.get('/api/schema/')
    assert res.status_code == 200
    assert 'openapi' in res.data
