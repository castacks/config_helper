
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
git submodule add https://github.com/castacks/config_helper.git
git submodule update --init --recursive
```

# General usage

## Types of configuration files

All configuration files should be in YAML format. There are two type of configuration files handled
by this package:

- __Base configuration:__ Ordinary YAML files with normal content.
- __Sweep configurations:__ YAML files with special keywords.

Here we have two types of keywords:

- __Sweep variable__: A keyword starts with `sweep@`. Its value is used to update values of
  DIFFERENT keys.
- __Key chain__: A keyword represented as a string in the format of `key0.key1.key2`. Its value is
  used to update a SPECIFIC key.

## Combine the configurations

The final configuration can be constructed from multiple base configurations and multiple/zero sweep
configurations. The use use the `--base_config` and `--sweep_config` commands to specify them. On
the command line. All base configurations will be merged. The order of the configurations appear in
the command line is important. During merging, the later configurations will override the earlier
ones if there is a key conflict. Similarly, all the sweep configurations are also merged in order.

## Sweep configurations

After the final sweep configuration is constructed by merging all sweep configurations in the
command line, all the key chains will be used to override any matching key hierarchies in the final
base configuration. For example, a key chain of

```yaml
key0.key1.key2: "string value"
```

will override/create the following key hierarchy in the final base configuration:

```yaml
key0:
    key1:
        key2: 123
```

After overriding all key chains, we perform variable sweeping. We keep a list of all the sweep
variables in the final sweep configuration. Then the base configuration is traversed. If a VALUE of
a key is a string starting with `sweep@`, then the value is replaced by the value recorded in the
list of sweep variables. For example, a sweep variable of

```yaml
sweep@batch_size: 1
```

will replace all the `sweep@batch_size` entries in the base configuration with the value `1`.

```yaml
data:
    batch_size: sweep@batch_size
visualization:
    batch_size: sweep@batch_size
```

## Embedded configuration

The user can embed a configuration file in another configuration file by setting a value to be a
string in the format of `key0.key1@/path/to/file.yaml`. The `/path/to/file.yaml` is the embedded
configuration. The prefix `key0.key1@` is optional. If it is present, then only the value of the key
`[key0][key1]` will be taken as the embedded content. 

Embedded configuration is expanded recursively such that there can be multiple levels of embedding.

Sweep variables can be used in any level of embedded configuration. Since variable sweeping happens
after key chain override, the user can also use embedded configuration in the sweep configuration as
the value of a key chain.

Note: a potential issue is that when a sweep variable points to an embedded configuration file,
however, that configuration also has a sweep variable. Currently, this situation is not handled. So
a rule of thumb: do not use a sweep variable to specify an embedded configuration file.

## Command line


# Example

```bash
python3 test_main.py \
    --config_base base_config_0.yaml \
    --config_base base_config_1.yaml \
    --config_sweep sweep_config_0.yaml \
    --config_sweep sweep_config_1.yaml \
    --config_sweep sweep_config_2.yaml \
    --config_name ./composed_config.yaml
```

# Contact

