# LAB06: CI Troubleshooting Guide

## Common Issues and Solutions

### Workflow Not Running

**Symptom:** You pushed code but no workflow appeared in the Actions tab.

**Causes and Solutions:**
1. **Wrong file location** - Workflow files must be in `.github/workflows/`. Check the path:
   ```bash
   # Should look like this
   .github/workflows/ci.yml
   ```
   Not in `github/` or `workflows/` directly.

2. **Syntax error in YAML** - Even a small indentation error prevents the workflow from loading. Check the Actions tab for error messages, or validate your YAML at [yamllint.com](https://www.yamllint.com/).

3. **Wrong branch filter** - If your workflow only triggers on `main` but you pushed to a different branch, it won't run:
   ```yaml
   on:
     push:
       branches: [ main ]  # Only runs on main branch
   ```

4. **Missing `on:` trigger** - Every workflow needs an event trigger.

---

### Tests Failing in CI but Passing Locally

**Symptom:** Tests pass on your machine but fail in GitHub Actions.

**Causes and Solutions:**

1. **Missing dependencies** - Your local environment may have packages installed globally that CI doesn't have. Always specify all dependencies in your `requirements.txt`:
   ```bash
   # Check what's installed and update requirements.txt
   pip freeze > requirements.txt
   ```

2. **Environment variables not set** - CI runs in a clean environment with no pre-set variables. Explicitly set any required environment variables:
   ```yaml
   - name: Run tests
     env:
       DATABASE_URL: postgresql://...  # Must be set explicitly
     run: python -m pytest
   ```

3. **Relative path issues** - CI runs from the repository root. Ensure your test commands use the correct working directory:
   ```yaml
   - name: Run admin tests
     working-directory: admin/python/test
     run: python run_tests.py
   ```
   Or use an explicit path change:
   ```yaml
   - name: Run admin tests
     run: |
       cd admin/python/test
       python run_tests.py
   ```

4. **File permissions** - Scripts may not be executable in CI. Use `python script.py` instead of `./script.py`, or add a chmod step.

5. **Different OS behavior** - GitHub-hosted runners use Ubuntu Linux. If you develop on macOS or Windows, there may be subtle differences in path separators or commands.

---

### Docker Build Failures

**Symptom:** Docker build fails in CI.

**Causes and Solutions:**

1. **Build context issues** - The `docker build` command must be run from the right directory:
   ```yaml
   # Building from repo root with a specific Dockerfile
   - name: Build image
     run: docker build -f admin/Dockerfile -t admin:ci .
   #                                                   ^ build context is repo root
   ```

2. **Base image not found** - Network issues or rate limiting from Docker Hub. Use `--pull` sparingly or authenticate:
   ```yaml
   - name: Login to Docker Hub
     uses: docker/login-action@v3
     with:
       username: ${{ secrets.DOCKERHUB_USERNAME }}
       password: ${{ secrets.DOCKERHUB_TOKEN }}
   ```

3. **Multi-stage build file copy errors** - Files referenced with `COPY` must exist relative to the build context. Review your Dockerfile paths.

4. **Out of disk space** - Large builds can exhaust the runner's disk. Free up space or use Docker build caching.

---

### Python Test Import Errors

**Symptom:** `ModuleNotFoundError` when running tests.

**Solution:** Ensure `sys.path` includes the module directories, or install the package. The test files in this project use:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

In CI, verify the working directory is set correctly:
```yaml
- name: Run Python tests
  run: |
    cd admin/python/test
    python run_tests.py
```

---

### YAML Indentation Errors

GitHub Actions uses strict YAML parsing. Common mistakes:

**Wrong - mixing tabs and spaces:**
```yaml
steps:
	- name: Step  # Tab character (invisible!)
    run: echo hello
```

**Wrong - inconsistent indentation:**
```yaml
steps:
  - name: Step one
    run: echo one
   - name: Step two    # 3 spaces instead of 2
     run: echo two
```

**Correct:**
```yaml
steps:
  - name: Step one
    run: echo one
  - name: Step two
    run: echo two
```

**Tip:** Use a YAML validator or an editor with YAML support (VS Code with the YAML extension).

---

### Job Dependency Issues

**Symptom:** Job starts before its dependency finishes, or doesn't run at all.

**Solution:** Use `needs:` to specify dependencies:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest

  build:
    needs: test          # This job only runs if 'test' passes
    runs-on: ubuntu-latest
    steps:
      - run: docker build .
```

---

### Service Containers Not Accessible

**Symptom:** Tests need a database or Redis but can't connect.

**Solution:** GitHub Actions supports **service containers** - Docker containers that run alongside your job:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost/testdb
        run: python -m pytest
```

Note: The service is accessible at `localhost` (not at the service name as in docker-compose).

---

### Workflow Taking Too Long

**Solutions:**

1. **Cache dependencies** - Use `actions/cache` to avoid re-downloading packages:
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

2. **Run jobs in parallel** - Jobs without `needs:` run concurrently.

3. **Limit test scope** - Use `pytest -k "not slow"` to skip slow tests in CI.

4. **Use `--fail-fast`** - Stop on first failure: `pytest --exitfirst`

---

### Permissions Issues

**Symptom:** Workflow can't write to the repository or create releases.

**Solution:** Add the necessary permissions to your workflow:
```yaml
permissions:
  contents: write      # For creating releases
  pull-requests: write # For commenting on PRs
  checks: write        # For reporting test results
```

Or grant specific permissions at the job level:
```yaml
jobs:
  build:
    permissions:
      contents: read
    runs-on: ubuntu-latest
    steps:
      # ...
```

---

## Debugging Tips

### Add Debug Output

```yaml
- name: Debug environment
  run: |
    echo "Current directory: $(pwd)"
    echo "Python version: $(python --version)"
    ls -la
    env | sort
```

### Enable Step Debug Logging

Set the secret `ACTIONS_STEP_DEBUG` to `true` in your repository settings to get verbose debug output.

### Re-run Failed Jobs

From the Actions tab, you can re-run failed jobs (useful when failures are due to flaky network issues).

### Check Runner Environment

```yaml
- name: Show runner info
  run: |
    uname -a
    df -h
    free -m
    docker --version
    python --version
```

## Getting Help

- Check the [GitHub Actions documentation](https://docs.github.com/en/actions)
- Search [GitHub Community discussions](https://github.com/orgs/community/discussions/categories/actions)
- Review workflow run logs carefully - the error message usually tells you exactly what went wrong
