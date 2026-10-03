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


