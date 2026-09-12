# Beginner's guide: run RichClub Explorer with Docker

This guide assumes no experience with Python, Docker, Git, or the command line.
Docker packages RichClub Explorer and all of its software dependencies together, so
you do not need to install Python or configure a programming environment.

## What you need

- A Windows, macOS, or Linux computer
- Docker Desktop or Docker Engine with Docker Compose
- A web browser
- An internet connection for the first build
- The RichClub Explorer project folder

The first build downloads a Python container and the required packages, so it may
take several minutes. Later launches are normally much faster.

## 1. Install and start Docker

### Windows

1. Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
2. Accept the WSL 2 installation or update prompts if Docker displays them.
3. Restart the computer if requested.
4. Open Docker Desktop and wait until it reports that the Docker engine is running.

### macOS

1. Download and install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/).
2. Choose the Apple silicon or Intel installer appropriate for the Mac. The Docker
   download page normally identifies the correct version.
3. Open Docker Desktop and wait until it reports that the Docker engine is running.

### Linux

Install [Docker Engine](https://docs.docker.com/engine/install/) and the Docker
Compose plugin for the Linux distribution. Start the Docker service before continuing.
If Docker reports a permission error, follow Docker's official
[Linux post-installation instructions](https://docs.docker.com/engine/install/linux-postinstall/)
or contact the local system administrator.

## 2. Download RichClub Explorer

Choose either method below. Git is useful for receiving updates, but it is not required.

### Option A: download with Git

Open Terminal on macOS/Linux or PowerShell on Windows, then run:

```bash
git clone https://github.com/adriennekline/richclub-explorer.git
cd richclub-explorer
```

### Option B: download without Git

1. Open the [RichClub Explorer repository](https://github.com/adriennekline/richclub-explorer).
2. Select **Code**, then **Download ZIP**.
3. Extract the ZIP archive.
4. Open a terminal in the extracted `richclub-explorer-main` folder:

   - **Windows:** Open the folder in File Explorer, click the address bar, type
     `powershell`, and press Enter.
   - **macOS:** Open Terminal, type `cd ` with a trailing space, drag the extracted
     folder into the Terminal window, and press Enter.
   - **Linux:** Open the folder in the file manager, right-click inside it, and select
     **Open in Terminal** when available.

## 3. Build and start the application

Confirm that Docker Desktop or Docker Engine is running. From inside the project
folder, run:

```bash
docker compose up --build
```

The command builds the container and starts Streamlit. Wait until the terminal shows
that the application is available. Keep this terminal window open while using the app.

Open the following address in a web browser:

**[http://localhost:8501](http://localhost:8501)**

`localhost` means the application is running on the same computer. No external web
server is required.

## 4. Run a first analysis

The application opens with a built-in example network, so no data file is needed for
the first run.

1. Leave **Data source** set to **Example network**.
2. Leave **Weighted analysis** turned off.
3. Leave **Richness measure** set to **degree**.
4. Select **100 null networks** for a quick demonstration.
5. Select **Run rich-club analysis**.

The results page displays:

- Network size, density, and connected-component information
- The observed rich-club coefficient and null-model envelope
- The normalized coefficient, \(\rho\)
- Empirical p-values and the number of rich nodes at each threshold
- Rich-club membership and rich-club, feeder, and local edges
- Buttons for downloading CSV tables, an SVG figure, and editable Methods text

Use at least **1,000 null networks** for a final scientific analysis. A normalized
coefficient above one is not sufficient evidence by itself; also examine the null
distribution, retained node count, threshold range, and robustness of the result.

## 5. Analyze your own network

In the sidebar, change **Data source** to **Upload CSV/TSV** and select the input type.

### Edge-list input

A binary edge list requires `source` and `target` columns:

```csv
source,target
gene_A,gene_B
gene_A,gene_C
gene_B,gene_C
```

A weighted edge list also includes a numeric `weight` column:

```csv
source,target,weight
gene_A,gene_B,0.82
gene_A,gene_C,0.71
gene_B,gene_C,0.77
```

Do not include the same undirected edge twice. For example, do not include both
`gene_A,gene_B` and `gene_B,gene_A`.

### Adjacency-matrix input

An adjacency matrix must be square and symmetric, with matching node labels in the
first row and first column. The diagonal must be zero:

```csv
,gene_A,gene_B,gene_C
gene_A,0,1,1
gene_B,1,0,1
gene_C,1,1,0
```

Version 0.1 supports simple, undirected networks. It rejects directed networks and
parallel edges rather than silently transforming them.

## Stop, restart, and run in the background

### Stop the application

In the terminal running the application, press `Ctrl+C`, then run:

```bash
docker compose down
```

### Restart without rebuilding

If the source code and dependencies have not changed:

```bash
docker compose up
```

### Run without keeping the terminal attached

```bash
docker compose up --detach
```

The application remains available at [http://localhost:8501](http://localhost:8501).
Stop a detached application with:

```bash
docker compose down
```

## Update to a newer version

If the project was cloned with Git:

```bash
git pull --ff-only
docker compose up --build
```

If the project was downloaded as a ZIP, download and extract the newest ZIP into a
new folder, open a terminal in that folder, and run `docker compose up --build` again.

## Useful diagnostic commands

Show whether the container is running:

```bash
docker compose ps
```

Display application logs:

```bash
docker compose logs
```

Follow new log messages as they appear:

```bash
docker compose logs --follow
```

Force a completely fresh image build:

```bash
docker compose build --no-cache
docker compose up
```

## Troubleshooting

### `docker: command not found`

Docker is not installed or the terminal has not recognized the installation. Install
Docker Desktop or Docker Engine, restart the terminal, and try again.

### `Cannot connect to the Docker daemon`

Docker Desktop or Docker Engine is not running. Start it, wait for the engine to become
ready, and rerun the command.

### `docker compose` is not recognized

Update Docker Desktop or install the Docker Compose plugin. Some older systems use
`docker-compose` with a hyphen, but the current recommended command is `docker compose`.

### Port 8501 is already in use

Another application is using the default port. Open `compose.yaml` in a text editor
and change:

```yaml
ports:
  - "8501:8501"
```

to:

```yaml
ports:
  - "8502:8501"
```

Run `docker compose up` again and open [http://localhost:8502](http://localhost:8502).

### The browser says it cannot connect

The first build may still be running. Wait until the terminal reports that Streamlit
is available. If the container stopped or the page remains unavailable, run:

```bash
docker compose ps
docker compose logs
```

The final log messages usually identify the problem.

### Changes are not appearing

Rebuild the container after updating the project:

```bash
docker compose down
docker compose up --build
```

If Docker continues to use stale build layers, use the fresh-build commands under
**Useful diagnostic commands**.

### Apple silicon computer

No configuration change should be necessary. The official Python image used by the
project supports both Apple silicon and standard x86-64 computers.

### Institutional network or proxy errors

The first build downloads a base image and Python packages. Institutional firewalls
or proxy settings may block those downloads. Consult local IT support for the approved
Docker proxy configuration.

## Data handling and privacy

The provided Compose configuration runs the application locally and does not create
a persistent Docker volume for uploaded data. Uploaded tables are processed inside
the running application and are not intentionally written to persistent container
storage. The original file remains wherever it was saved on the computer.

Stopping and removing the container clears its temporary writable layer. Do not expose
the application port publicly or use confidential or regulated data in an externally
hosted deployment without the appropriate institutional review and safeguards.

## Remove the local application

Stop and remove the container:

```bash
docker compose down
```

Remove the locally built image if it is no longer needed:

```bash
docker image rm richclub-explorer:local
```

The downloaded project folder can then be deleted normally. Docker Desktop itself
does not need to be removed unless it is no longer wanted for other applications.
