
A helper Python package for dynamically merging and modifying configuration files

# Introduction

config_helper is a Python package that helps the user to dynamically merge and modify configuration
files. The reasons behind this package could be:

- We can share a base configuration and add modification/augmentation on top of it for different
  purposes while keeping the original base configuration unchanged.
- We can have a hierarchical configuration system where later configurations can be built on top of
  earlier ones.

A great use case for our research activities is to have a base configuration for training a deep
neural network. Then during testing, we can have different configurations, e.g., when the dataset
changes, by only augmenting the relevant parts, keeping all other training settings unchanged. When
we decide to change some training parameters that are in the base configuration, the changes will be
automatically reflected during testing, as long as these parameters are not override in the
augmented configuration. 

Certain functionalities of this package are inspired by the initial codes done by Conner Pulling
[cpulling@andrew.cmu.edu](mailto:cpulling@andrew.cmu.edu).

# Use as a Git submodule

This package is designed to be used as a Git submodule. To add it to your project

```bash
cd <your awesome project path>
git submodule add 
```

# General usage

# Contact

