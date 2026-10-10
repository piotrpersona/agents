# Research

> note: these are general guidelines for ML, research and data processing tasks, some of them map to the Python guidelines above, but are more specific to ML and data processing tasks

In research mode use `/caveman` only to report task status, never to explain concepts.

## Environment

- polars
- scikit-learn
- numpy
- plotly
- ipykernel
- jupyter
- boto3
- datasets
- transformers
- umap
- hdbscan
- torch
- mlflow

## Coding Preferences

- use polars for data processing, avoid using pandas for large datasets
- always plot charts using plotly, avoid using matplotlib
    - always add title and axis labels to the charts
    - prefer pastel pallete
    - for confusion matrices use hot/cold color scheme - hot high accruacy, cold low accuracy
        - report accuracy, f1, f1macro, precision, recall and  support for each class in the confusion matrix
    - for sunburst charts use prism pallete
    - when visualizing embeddings use umap for dimensionality reduction and hdbscan for clustering, avoid using t-SNE for dimensionality reduction
        - prefer using scatter plots for visualizing embeddings, avoid using line plots for visualizing embeddings
        - always define a fixed pallete for visualizing embeddings, avoid using random colors for visualizing embeddings
            - when specified save it locally for next runs for same kind of dataset
    - for sankey go left-right orientatation and ensure that nodes are spread
- don't write tests in research code unless specified
- prefer using multithreading for data processing tasks, avoid using multiprocessing unless specified
    - for example fetching data from S3 or other external sources, use multithreading to fetch data in parallel
    - especially if task needs high concurrency it can be rewritten to Go and use goroutines and channels for concurrency and single main.go script
    - prefer using async/await for I/O bound tasks, avoid using threads for I/O bound tasks 
- when implementing training jobs or scripts that process n records and perform some measurements always support canary mode, where:
    - user can run numeric number of samples like: 100 or 1000 and percentage 1% or 10%
    - when running experiments always start with a default of 100 records canary before proceeding to full run - inform user about it with `/caveman`

## Models

- when using models always define device and use `.to(device)`
    - always output which device is used
- when exporting models to different formats always implement unit test to verify the export, outputs and compare

## Training
- always use early  stopping and model checkpointing, save the best model based on the selected criterion - always prompt if not specified
- when training classificaiton models always implement logging per-epoch and val/train metrics:
    - loss, class, accuracy, f1, f1macro, precision, recall and support global and for each class

## Experiment tracking

- track every ML experiment in MLflow - a training or measurement run that is not logged did not happen
- one experiment per research question, one run per config, name runs so they can be told apart
- log per run:
    - params - full config, seed, model name, dataset name, time range, split sizes
    - metrics per epoch - the same train/val metrics listed above
    - artifacts - plotly html charts, confusion matrices, classification reports, the config file
    - tags - canary vs full run, git commit, dataset version
    - device, GPU model and count, and the GPU utilisation summary
- use `mlflow.autolog()` where the framework supports it and log explicitly whatever autolog misses
- log the model with its MLflow flavor and register the best checkpoint by the selected criterion
- read `MLFLOW_TRACKING_URI` from `.env`, never hardcode it
- keep canary runs tagged so they stay out of comparisons

## GPU

- always report the device in use plus GPU model, count, total and free memory at job start
- use every visible GPU - multi-GPU runs go through DDP (`torchrun`), never leave a device idle
- saturate the GPU, target near 100% utilisation:
    - tune batch size up to the memory limit, log the peak memory used
    - use mixed precision (bf16 preferred, fp16 as fallback) and `torch.compile` where it helps
    - keep data loading off the hot path - `DataLoader` with `num_workers`, `pin_memory`, prefetch
    - move preprocessing to the GPU or precompute it, never block the loop on CPU work
- log GPU utilisation and memory alongside the per-epoch metrics, and print a summary at the end
- test GPU usage, do not assume it:
    - assert the accelerator is available and fail fast instead of silently falling back to CPU
    - sample utilisation during a short canary run and report it - flag any run that stays low
    - verify utilisation and memory with `nvidia-smi` on the host and report what it shows

## Cloud GPUs

- use SkyPilot for all cloud GPU work - dev clusters, fine-tuning, distributed training, sweeps and serving
- the SkyPilot skill owns the CLI and YAML details, install it once per machine:
    - `claude plugin marketplace add skypilot-org/skypilot`
    - `claude plugin install skypilot@skypilot`
    - ask for "Bootstrap SkyPilot" to install the CLI and set up cloud credentials
- compare GPU prices across clouds before picking one and configure multi-cloud failover
- prefer spot instances with preemption recovery, checkpoint often so a preempted job resumes
- set auto-stop on dev clusters and tear down clusters when the run is done
- keep cloud credentials in the environment, never in the task YAML

## Dataset

> IMPORTANT

These apply to all kind of data that is used for research, not only training.
Working with datasets require a bit more Q&A from you.
You need to recognize that we are doing research or measuring data trends or the user will tell you.
In research mode you must clarify the data to be explored by asking questions about the dataset.
It is crucial to have full understanding of the data characteristics before beginning a research - this will be useful for planning the experiments.

Questions and topics that will help describe the data:
- dataset name and purpose
- time range - must be absolute and scoped with both dates, [start, end] - always use inclusive ≤≥, never use exclusive <>, unless asked to
- number of samples and breakdown 
- record id and record date must be present - these are crucial properties
- always verify if the dataset is stratified
    - at least by record date
    - preferably by customer_id, data_type, or other distinct properties 
    - if it cannot be verified suggest how to fix it withing the code (like fixing SQL query) or ask user to do it as a last resort
- when training models always use stratified sampling for train/val/test splits - never use random sampling, unless asked to do
- pay attention to imbalance of the data and inform it to user
- always present breakdown of the dataset by date and other stratification properties and by split
- when visualizing datasets use a simple plotly python script, export to html and automatically open in browser

### Credibility and data-quality tooling

- separate the two questions before sampling: an unbiased *measurement* needs a
  representative sample (stratified by real production frequency); *finding holes*
  needs a diverse/adversarial sample - never mix them in one set
- measuring effectiveness needs ground truth: a trusted reference + an explicit
  "what counts as correct" rule + who adjudicates (inter-annotator agreement) -
  a cluster id is structure, never a label of truth
- when the data has a time axis, split by time (past → future), not randomly
- tools automate detection, never the construct definition or the
  representative-vs-diverse choice - those stay with the researcher:
    - cleanlab - label noise / mislabeled samples
    - deepchecks, evidently - data integrity, distribution drift, train/test leakage
    - pandera, Great Expectations - schema and distribution checks
    - Lilac, Nomic Atlas - embedding-space dataset exploration; SemDeDup for near-duplicates
    - Vendi score / coverage - diversity as a single number

### Embedding plots and cluster validation

- a UMAP/t-SNE scatter is a sanity-check sketch, never evidence: it preserves
  local neighbourhoods only - inter-cluster distances, cluster size and density
  are not meaningful (in t-SNE they are artefacts of perplexity)
- never read a 3D rotation as separation - a flattering angle always exists;
  prefer 2D with hover (inspect the real sample) over a rotating 3D plot, and
  caption any projection "distances not meaningful"
- back every "there are clusters/families" claim with metrics computed in the
  ORIGINAL embedding space, never on the 2D/3D coordinates (the projection
  distorts them):
    - silhouette, Davies-Bouldin, Calinski-Harabasz - compactness and separation
    - purity / ARI / NMI vs labels when GT exists - do clusters map to real classes
    - stability - re-cluster over seeds/subsamples, check the same families recur
- cluster with HDBSCAN (allows noise / no-cluster points) over k-means, which
  forces every point into a cluster
- flow: cluster in embedding space → validate (silhouette + stability + purity)
  → 2D UMAP only to illustrate


