# LAB06: Continuous Integration with GitHub Actions

## Learning Objectives

By completing this assignment, you will:

- Understand what Continuous Integration (CI) is and why it matters
- Create GitHub Actions workflow files from scratch
- Automatically run your existing test suite on every push
- Build Docker images in CI to catch integration issues early
- Interpret CI results and fix failing workflows
- Follow best practices for CI configuration

## Overview

In previous labs you built the ImgCloud application with tests included. Running those tests manually every time is error-prone - developers forget, or only run "their" tests. CI solves this by automatically running all tests every time code is pushed.

In this lab you will add a CI pipeline to your repository using **GitHub Actions**. The pipeline will:

1. **Run unit tests** for the frontend service
2. **Build Docker images** to verify the application compiles and packages correctly

Before writing any YAML, read [LAB06-GITHUB-ACTIONS.md](LAB06-GITHUB-ACTIONS.md) to understand how GitHub Actions works.

## Prerequisites

- A working LAB04 codebase (frontend + imgprocessor + docker-compose.yml)
- A GitHub repository with your project code

### Don't Have a Working Lab04 Base?

A complete Lab04 docker-compose solution is provided in `labs/lab06/docker-compose-lab04.yml`. To use it as your starting point:

```bash
cp labs/lab06/docker-compose-lab04.yml docker-compose.yml
```

Then replace `STUDENTNAME` with your username and set `YOUR_PORT` from `PORTS.md` before continuing.

See [LAB04-STARTING-POINT.md](LAB04-STARTING-POINT.md) for details.

### Tests You Will Automate

The frontend test files already exist in the repository:
- `frontend/test_empty_params.py` - Tests empty form parameter handling
- `frontend/test_form_submission.py` - Tests form submission with mocked gRPC

## Getting Started

### 1. Understand Your Existing Tests

Before writing CI, you need to know what you are automating. Run the existing tests locally to make sure they pass.

First, set up a local Python virtual environment and install dependencies. A virtual environment isolates your project's packages from your system Python — this is the recommended approach for local runs so that installed packages don't conflict with other projects or your system Python installation.

> **Note:** The virtual environment is only needed for running tests locally. GitHub Actions CI uses an isolated runner environment managed by `actions/setup-python`, and Docker has its own isolated container environment — neither needs a virtual environment.

```bash
cd frontend
python3 -m venv venv          # creates frontend/venv/
source venv/bin/activate      # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **`python3` vs `python`:** On Linux/macOS, use `python3` to invoke Python 3 explicitly. In your CI workflow, after the `actions/setup-python` step, the runner makes the configured version available as simply `python` — so your CI YAML uses `python`, not `python3`.

Then generate the gRPC protobuf code that `app.py` imports (this must be done before tests can run):

```bash
python3 -m grpc_tools.protoc \
  -I../imgprocessor \
  --python_out=. \
  --grpc_python_out=. \
  ../imgprocessor/image_processor.proto
```

Then run the tests:

```bash
python3 -m pytest test_empty_params.py test_form_submission.py -v
```

Make sure all tests pass locally before moving on. If any tests fail locally, fix them first - CI cannot pass if the tests are broken.

### 2. Create the Workflow Directory

GitHub Actions workflows must live in a specific directory:

```bash
mkdir -p .github/workflows
```

This directory must be at the **root of your repository**, not inside a subdirectory.

### 3. Plan Your Workflow

Before writing the YAML file, plan what your CI should do:

**Questions to answer:**
1. When should CI run? (on every push? only on certain branches? on pull requests?)
2. What jobs do you need? (one job for everything, or separate jobs for different concerns?)
3. What steps does each job need? (checkout, install dependencies, run tests)
4. What environment variables do tests need?

**Suggested workflow structure:**

```
CI Workflow
├── Job: test-python-frontend
│   ├── Step: Checkout code
│   ├── Step: Set up Python 3.11
│   ├── Step: Install frontend dependencies
│   ├── Step: Generate gRPC protobuf code
│   └── Step: Run frontend tests
│
└── Job: build-docker
    ├── Step: Checkout code
    └── Step: Build frontend Docker image
```

Each job runs independently on a fresh Ubuntu runner.

### 4. Create Your Workflow File

Create a file at `.github/workflows/ci.yml`. Your workflow file needs:

**Trigger section (`on:`):**
- Run on pushes to `main`
- Run on pull requests targeting `main`

Look up the GitHub Actions syntax for triggering on push and pull_request events. The [LAB06-GITHUB-ACTIONS.md](LAB06-GITHUB-ACTIONS.md) background document has examples.

**Jobs section (`jobs:`):**

For each job, you need:
1. A `runs-on:` specifying the runner (use `ubuntu-latest`)
2. A `steps:` list

**Required steps in every job:**
- Checkout your repository code using the `actions/checkout@v4` action

**Setting up Python:**
- Use the `actions/setup-python@v5` action
- Specify Python version `'3.11'`

**Installing dependencies:**
- Use the `run:` keyword to execute shell commands
- Use `pip install -r path/to/requirements.txt`

**Running tests:**
- For frontend: `python -m pytest test_empty_params.py test_form_submission.py -v`
- Pay attention to the **working directory** for the test command

**Building Docker:**
- Use `docker build` with the correct `-f` flag to specify the Dockerfile
- The frontend Dockerfile is at `frontend/Dockerfile`
- The build context should be the repository root (`.`)

### 5. Understanding the Frontend Test Requirements

The frontend tests (`test_form_submission.py` in particular) import from `app.py`, which in turn imports the generated gRPC protobuf code:

```python
import image_processor_pb2        # These are generated files
import image_processor_pb2_grpc   # (not committed to the repo)
```

These files must be **generated** before tests can run. The proto definition is at `imgprocessor/image_processor.proto`. To generate the Python code:

```bash
cd frontend
python -m grpc_tools.protoc \
  -I../imgprocessor \
  --python_out=. \
  --grpc_python_out=. \
  ../imgprocessor/image_processor.proto
```

`grpc_tools` is part of the `grpcio-tools` package, which is already in `frontend/requirements.txt`. Your CI workflow must include this generation step **before** running the frontend tests.

This is a common CI pattern: generating code from schema files (protobuf, OpenAPI, etc.) as part of the build step.

### 6. Working with Environment Variables in Tests

Review the test files to understand what environment they need:

- `test_empty_params.py` - Pure Python logic tests, no environment variables needed
- `test_form_submission.py` - Mocks gRPC, no real services needed

This means the frontend unit tests pass in CI without any running database, Redis, or image processor.

### 7. Push and Verify

Once you have written your workflow file, commit and push it to `main`:

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI workflow"
git push origin main
```

As soon as the push lands on `main`, GitHub detects that `.github/workflows/ci.yml` was added. Because your workflow is configured with `on: push: branches: [main]`, GitHub Actions automatically queues a workflow run for that commit. No extra steps are needed — the trigger fires the moment the file exists on the branch.

To see the result:
1. Go to your GitHub repository
2. Click the **Actions** tab — you will see a run listed for your commit, either in progress or completed
3. Click the run to see all jobs
4. Click a job to see each step's output, including the test results
5. A green checkmark ✅ means the job passed; a red ✗ means it failed

A status icon will also appear next to the commit in the commit history once the run completes.

> For a detailed explanation of how workflow runs are displayed and navigated, see [LAB06-GITHUB-ACTIONS.md — Checking Workflow Status](LAB06-GITHUB-ACTIONS.md#checking-workflow-status).

### 8. Fix Failing Workflows

If your workflow fails:
1. Read the full error output in the GitHub Actions UI
2. Identify which step failed
3. Check [LAB06-TROUBLESHOOTING.md](LAB06-TROUBLESHOOTING.md) for common issues
4. Fix the issue in your workflow file
5. Push again - the new commit will automatically trigger another workflow run

Common things to verify:
- Are all file paths correct relative to the repository root?
- Is the working directory set correctly for the test command?
- Is the protobuf generation step placed **before** the test step?
- Are all required dependencies installed?
- Is the Python version correct?

## Workflow Design Considerations

### Single Job vs. Multiple Jobs

**Single job (simpler, but slower feedback):**
```
test-and-build:
  - generate protobuf
  - run tests
  - build docker image
```

**Multiple jobs (better feedback, faster overall):**
```
test-frontend: generates protobuf, runs tests
build-docker: builds Docker image only after tests pass
```

With separate jobs, the Docker build doesn't waste time if tests fail.

### When to Build Docker

You have two options:

**Option A:** Always build Docker (to catch build errors early)
**Option B:** Only build Docker when tests pass (saves time if tests fail)

Use the `needs:` keyword to make the Docker build job depend on the successful test job.

### Caching to Speed Up CI

Re-downloading Python packages on every run takes time. Research the `actions/cache@v4` action and how to use it with pip's cache directory. This is optional but good practice.

## REST Endpoints to Check (Optional)

If you want to go further, you can add a job that starts the Docker container and verifies the health endpoint responds:

```bash
# Build and start the frontend container
docker run -d -p 8080:8080 frontend:ci

# Wait for it to start
sleep 5

# Verify the health endpoint responds
curl -f http://localhost:8080/health
```

Note that the full health response will show the processor, MinIO, Redis, and database as "unavailable" since those services are not running - that is expected for a basic build verification. The goal is just to confirm the image builds and the server starts.

For a full integration test with all services, see the [GitHub Actions documentation on service containers](https://docs.github.com/en/actions/using-containerized-services/about-service-containers).

## Submission

When complete, your repository should have:

1. **`.github/workflows/ci.yml`** - Your CI workflow file
2. **Passing workflow runs** visible in the Actions tab
3. **Green status icons** ✅ visible next to commits in the commit history

Tag your final submission:
```bash
git add .github/workflows/ci.yml
git commit -m "Complete Lab06 CI"
git tag lab06-final
git push origin main --tags
```

## Additional Resources

- [LAB06-GITHUB-ACTIONS.md](LAB06-GITHUB-ACTIONS.md) - GitHub Actions concepts and syntax
- [LAB06-TROUBLESHOOTING.md](LAB06-TROUBLESHOOTING.md) - Common problems and solutions
- [LAB04-STARTING-POINT.md](LAB04-STARTING-POINT.md) - Lab04 starting base (docker-compose-lab04.yml)
- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Workflow syntax reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [actions/checkout](https://github.com/actions/checkout)
- [actions/setup-python](https://github.com/actions/setup-python)
- [actions/cache](https://github.com/actions/cache)
