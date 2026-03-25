# LAB06: GitHub Actions Background

## What is Continuous Integration (CI)?

**Continuous Integration (CI)** is the practice of automatically building and testing code every time a developer pushes changes to a shared repository. The goal is to detect integration problems early, when they are cheapest to fix.

Key benefits:
- **Fast feedback** - Know within minutes if your change broke something
- **Consistency** - Tests run in a clean, reproducible environment every time
- **Confidence** - Merge changes knowing they passed automated checks
- **Visibility** - Team can see the health of the codebase at any time

## What is GitHub Actions?

**GitHub Actions** is GitHub's built-in CI/CD platform. It lets you automate workflows directly in your repository using YAML configuration files.

### Core Concepts

#### Workflows
A **workflow** is an automated process defined in a YAML file. Workflows live in the `.github/workflows/` directory of your repository.

```
.github/
└── workflows/
    ├── ci.yml          # Your CI workflow
    └── deploy.yml      # Another workflow
```

#### Events (Triggers)
Workflows run in response to **events** in your repository. Common events:

| Event | When it fires |
|-------|---------------|
| `push` | When code is pushed to a branch |
| `pull_request` | When a PR is opened, updated, or synchronized |
| `workflow_dispatch` | Manually triggered from the GitHub UI |
| `schedule` | On a cron schedule |

Example trigger configuration:
```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

#### Jobs
A **job** is a set of steps that run on the same runner. Jobs run in parallel by default (unless you specify dependencies with `needs:`).

```yaml
jobs:
  job-one:
    runs-on: ubuntu-latest
    steps:
      # ...

  job-two:
    runs-on: ubuntu-latest
    needs: job-one    # Wait for job-one to finish
    steps:
      # ...
```

#### Steps
A **step** is an individual task within a job. Steps run sequentially. Each step is either:
- A **shell command** using `run:`
- An **action** using `uses:`

```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4          # Use a pre-built action

  - name: Install dependencies
    run: pip install -r requirements.txt  # Run a shell command

  - name: Run tests
    run: python -m pytest -v
```

#### Runners
A **runner** is the server that executes your jobs. GitHub provides hosted runners:
- `ubuntu-latest` - Ubuntu Linux (most common)
- `windows-latest` - Windows Server
- `macos-latest` - macOS

#### Actions
**Actions** are reusable units of code that you can use in your steps. GitHub maintains many official actions, and the community contributes thousands more.

Common official actions:
- `actions/checkout@v4` - Checks out your repository code
- `actions/setup-python@v5` - Sets up a Python environment
- `actions/cache@v4` - Caches files between workflow runs

---

### Using `actions/checkout@v4`

The checkout action clones your repository onto the runner so subsequent steps can access your code. It must be the first step in virtually every job.

**For CI workflows (including this lab), the bare form is all you need:**
```yaml
- name: Checkout code
  uses: actions/checkout@v4
```

When a workflow runs on a `push` event, GitHub Actions automatically knows which commit triggered it and checks out that commit. When it runs on a `pull_request` event, it checks out a merged version of the PR branch onto the target branch. You do **not** need to specify a `ref` for standard CI.

**When would you specify a `ref`?**
Only in advanced scenarios outside normal CI testing:
- Deploying a specific tagged release to production
- A workflow that builds documentation from the `gh-pages` branch while testing code on `main`
- Cross-repository workflows that need to check out a different repo

**Available parameters (for reference):**

| Parameter | Purpose | When to use |
|-----------|---------|-------------|
| `fetch-depth` | Number of commits to fetch (`0` = full history) | When your tooling needs git history (e.g., changelog generators) |
| `ref` | Branch, tag, or SHA to check out | Only needed for non-standard checkouts; leave unset for CI |
| `path` | Check out into a subdirectory | When checking out multiple repos in one job |
| `token` | PAT for private repos or triggering workflows | Only for advanced cross-repo scenarios |

---

### Using `actions/setup-python@v5`

This action installs a specific Python version on the runner and adds it to `PATH`, so `python` and `pip` commands use it.

**For this lab, you need `python-version` — that's the main parameter:**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
```

**Available parameters (for reference):**

| Parameter | Purpose | When to use |
|-----------|---------|-------------|
| `python-version` | Version to install (`'3.11'`, `'3.11.x'`, etc.) | **Required** for every use |
| `cache` | Built-in pip caching shortcut | Use `'pip'` as an alternative to `actions/cache` |
| `cache-dependency-path` | Path to requirements file for the built-in cache key | Only when using `cache: 'pip'` with a non-default requirements location |
| `architecture` | CPU architecture (`x64`, `x86`) | Rarely needed; `x64` is the default on all hosted runners |

**Example - using the built-in pip cache (simpler than `actions/cache`):**
```yaml
- name: Set up Python 3.11
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
    cache-dependency-path: 'myapp/requirements.txt'
```

The `cache: 'pip'` shortcut is an alternative to configuring `actions/cache` manually. Both approaches work — the `actions/cache` approach (covered in the next section) gives you more control over what gets cached.

**Matrix builds (for reference — testing multiple Python versions at once):**
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

For this lab, a single Python version is all you need.

---

### Using `actions/cache@v4`

The cache action saves and restores files between workflow runs. This avoids re-downloading large dependency sets on every run. For this lab, caching pip packages is the most relevant use.

**How it works:**
1. Before your install step, the action checks if a cache exists for the given `key`
2. If a cache hit occurs, files are restored and the install step is much faster
3. After the job, any new files at the `path` are saved under the `key`

**For pip (Python packages) — what you need for this lab:**
```yaml
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

Place this step **before** your `pip install` step. When the cache hits, `pip install` runs in seconds instead of minutes.

**Key parameters:**

| Parameter | Purpose | Notes |
|-----------|---------|-------|
| `path` | File/directory to cache | `~/.cache/pip` for pip |
| `key` | Unique cache identifier; if it changes, a new cache is created | Use `hashFiles(...)` so it invalidates when requirements change |
| `restore-keys` | Fallback keys to try if `key` doesn't match exactly | Acts as a prefix match for partial hits |

**Cache key strategy:**
- Include `runner.os` so Linux/macOS/Windows don't share caches
- Use `hashFiles(...)` so the cache invalidates when requirements change
- `restore-keys` provides a partial hit when the exact hash hasn't been cached yet

**Example - caching pip when requirements file is in a subdirectory:**
```yaml
- name: Cache pip
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('frontend/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

**For reference — caching npm packages works the same way:**
```yaml
- name: Cache node_modules
  uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-npm-${{ hashFiles('package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-npm-
```

---

### Using `docker/setup-buildx-action@v3`

Docker Buildx is an extended build client that adds features to `docker build`, including build caching, multi-platform builds, and better performance.

**Why use it?** The standard `docker build` command does not support all caching backends. Buildx enables `type=gha` (GitHub Actions cache) for Docker layer caching, which makes repeated builds significantly faster.

**For this lab, no parameters are needed — just add the step before your build:**
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```

This prepares the builder. The next step (`docker/build-push-action`) uses it automatically.

---

### Using `docker/build-push-action@v5`

This action builds a Docker image using Buildx and optionally pushes it to a registry. For this lab, you will use it to **build only** (no push) to verify your image compiles correctly.

**For this lab — build only, no push:**
```yaml
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    file: path/to/Dockerfile
    push: false
    tags: myapp:ci
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

The three key parameters to understand for this lab:
- `context` — the build context directory (the `.` at the end of a normal `docker build .` command)
- `file` — path to the Dockerfile (default is `Dockerfile` in the context directory)
- `push: false` — builds the image locally on the runner, does not push it anywhere

**Available parameters (for reference):**

| Parameter | Purpose | When to use |
|-----------|---------|-------------|
| `context` | Build context directory | **Required** — set to `.` for repository root |
| `file` | Path to Dockerfile | Only needed when the Dockerfile is not `{context}/Dockerfile` |
| `push` | Push to registry after build | Set to `false` for CI build verification; `true` for deployment |
| `tags` | Image name and tag(s) | **Required** |
| `cache-from` | Where to read layer cache from | `type=gha` to use GitHub Actions cache |
| `cache-to` | Where to write layer cache to | `type=gha,mode=max` |
| `build-args` | Build-time variables (like `--build-arg`) | When your Dockerfile uses `ARG` |
| `platforms` | Target platforms for multi-arch builds | Advanced — not needed for this lab |

**Example - build and push to Docker Hub (for reference, not needed for this lab):**
```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myusername/myapp:latest
```

---

### Workflow YAML Structure

Here is the complete structure of a workflow file:

```yaml
name: Descriptive Name          # Workflow name (shown in GitHub UI)

on:                             # When to run this workflow
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:                           # One or more jobs
  job-name:                     # Unique identifier for this job
    runs-on: ubuntu-latest      # Which runner to use

    steps:                      # Ordered list of steps

      - name: Step description  # Human-readable step name
        uses: actions/checkout@v4  # Use a pre-built action

      - name: Another step
        run: |                  # Multi-line shell command
          echo "Hello, World!"
          ls -la
```

### Environment Variables

You can set environment variables at the workflow, job, or step level:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DATABASE_URL: postgresql://user:pass@localhost/test
    steps:
      - name: Run tests
        run: python -m pytest
        env:
          TEST_ONLY_VAR: some_value
```

### Caching Dependencies

See the [detailed guide above](#using-actionscachev4) for full cache configuration options. Quick reference:

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Secrets

For sensitive values (passwords, API keys), use **GitHub Secrets**:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add a new secret
3. Reference it in your workflow:

```yaml
- name: Deploy
  env:
    API_KEY: ${{ secrets.MY_API_KEY }}
  run: ./deploy.sh
```

### Checking Workflow Status

After pushing, you can see your workflow runs:
1. Go to your GitHub repository
2. Click the **Actions** tab
3. Click on a workflow run to see details
4. Click on a job to see individual step output

A green checkmark ✅ means the job passed. A red ✗ means it failed.

### Matrix Builds

Test across multiple configurations using a **matrix strategy**:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pytest
```

This creates three separate test jobs, one for each Python version.

## GitHub Actions for Docker

Docker images can be built using either the standard `docker build` command or the `docker/build-push-action` (see [detailed guide above](#using-dockerbuild-push-actionv5)).

**Simple build using shell command:**
```yaml
- name: Build Docker image
  run: docker build -t myimage:latest .

- name: Test the image
  run: |
    docker run --rm myimage:latest python -m pytest
```

**Build with caching using the action (recommended):**
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and cache
  uses: docker/build-push-action@v5
  with:
    context: .
    push: false
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

## Workflow File Validation

Before committing, you can validate your workflow YAML:

1. **GitHub's built-in validation** - Push your workflow file; GitHub will report syntax errors in the Actions tab
2. **actionlint** - A command-line linter for GitHub Actions workflows
3. **VS Code extension** - The "GitHub Actions" extension provides syntax highlighting and validation

## Additional Resources

- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [GitHub Actions marketplace](https://github.com/marketplace?type=actions)
- [Workflow syntax reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Starter workflows](https://github.com/actions/starter-workflows)
