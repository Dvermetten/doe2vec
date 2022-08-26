import os

import numpy as np
from datasets import Dataset
from huggingface_hub import push_to_hub_keras
from huggingface_hub import upload_file
from doe2vec import doe_model
import tensorflow as tf

model_type = "VAE"
kl_weight = 0.001
seed = 0
dir = "../models"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
tf.config.experimental.enable_tensor_float_32_execution(False)
for d in [2]:
    for m in [8]:
        for latent_dim in [24]:
            obj = doe_model(
                d,
                m,
                n=d * 50000,
                latent_dim=latent_dim,
                kl_weight=kl_weight,
                use_mlflow=False,
            )
            if not obj.load("../models/"):
                obj.generateData()
                obj.compile()
                obj.fit(100)
                obj.save("../models/")
            data = np.load(
                f"{dir}/data_{d}-{m}-{latent_dim}-{seed}-{model_type}{kl_weight}.npy"
            )
            functions = np.load(
                f"{dir}/functions_{d}-{m}-{latent_dim}-{seed}-{model_type}{kl_weight}.npy"
            )
            datadict = {
                "y": data[:250000],
                "function": functions,
                "array_x": [obj.sample] * len(functions),
            }
            dataset = Dataset.from_dict(datadict)
            print(dataset)
            push_to_hub_keras(
                obj.autoencoder,
                f"doe2vec-d{d}-m{m}-ls{latent_dim}-{model_type}-kl{kl_weight}",
            )  # , repo_url="https://huggingface.co/BasStein/doe2vec-d2-m8-ls16")
            dataset.push_to_hub(
                f"doe2vec-d{d}-m{m}-ls{latent_dim}-{model_type}-kl{kl_weight}"
            )
            readme = f"""---
language:
- en
license: apache-2.0
library_name: keras
tags:
- doe2vec
- exploratory-landscape-analysis
- autoencoders
datasets:
- doe2vec-d{d}-m{m}-ls{latent_dim}-{model_type}-kl{kl_weight}
metrics:
- mse
---

## Model description

DoE2Vec model that can transform any design of experiments (function landscape) to a feature vector.  
For different input dimensions or sample size you require a different model.  
Each model name is build up like doe2vec-d{{dimension\}}-m{{sample size}}-ls{{latent size}}-{{AE or VAE}}-kl{{Kl loss weight}}

Example code of loading this huggingface model using the doe2vec package.

First install the package

    pip install doe2vec

Then import and load the model.


    from doe2vec import doe_model

    obj = doe_model(
        {d},
        {m},
        latent_dim={latent_dim},
        kl_weight={kl_weight},
        model_type="{model_type}"
    )
    obj.load_from_huggingface()
    #test the model
    obj.plot_label_clusters_bbob()

## Intended uses & limitations

The model is intended to be used to generate feature representations for optimization function landscapes.
The representations can then be used for downstream tasks such as automatic optimization pipelines and meta-learning.


## Training procedure

The model is trained using a weighed KL loss and mean squared error reconstruction loss.
The model is trained using 250.000 randomly generated functions (see the dataset) over 100 epochs.

co2_eq_emissions:
  emissions: 0.0363
  source: "code carbon"
  training_type: "pre-training"
  geographical_location: "Leiden, The Netherlands"
  hardware_used: "1 Tesla T4"
"""
            text_file = open("README.md", "wt")
            n = text_file.write(readme)
            text_file.close()
            upload_file(
                path_or_fileobj="README.md", 
                path_in_repo="README.md", 
                repo_id= f"BasStein/doe2vec-d{d}-m{m}-ls{latent_dim}-{model_type}-kl{kl_weight}"
            )
