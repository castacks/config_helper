
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
automatically reflected during testing, as long as these parameters are not overridden in the
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

## Command line

```
python3 <your_awesome_python_script.py> \
  --base_config base_config_file_0 \
  --base_config base_config_file_1 \
  ...
  --base_config base_config_file_N
  --sweep_config sweep_config_file_0 \
  --sweep_config sweep_config_file_1 \
  ...
  --sweep_config sweep_config_file_M \
  --config_name <filename for saving the final config to file system>
  <other options>
```

There could be multiple `--base_config` arguments and zero or multiple `--sweep_config` arguments.
Their usage is described later. Use `--config_name` to specify a file path for saving the final configuration file to the file system.

## Types of configuration files

All configuration files should be in YAML format. There are two types of configuration files handled
by this package:

- __Base configuration:__ Ordinary YAML files with normal content.
- __Sweep configurations:__ YAML files with special keywords.

Here we have two types of keywords:

- __Sweep variable__: A keyword starts with `sweep@`. Its value is used to update the values of
  DIFFERENT keys.
- __Key chain__: A keyword represented as a string in the format of `key0.key1.key2`. Its value is
  used to update a SPECIFIC key.

## Combine the configurations

The final configuration can be constructed from multiple base configurations and multiple/zero sweep
configurations. The user uses the `--base_config` and `--sweep_config` commands to specify them on
the command line. All base configurations will be merged. The order of the configurations that appear in
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
after key chain override, the user can also use an embedded configuration in a sweep configuration as
the value of a key chain.

Note: a potential issue is that when a sweep variable points to an embedded configuration file,
however, that configuration also has a sweep variable. Currently, this situation is not handled. So
a __rule of thumb: do not use a sweep variable to specify an embedded configuration file__.

# Example

The best way to illustrate how config_helper works is by using an example. We have a set of 
simple configuration files in the [test](test) folder. These configurations represent a typical 
scenario where a deep-learning model goes through training and validation separately with 
different settings. To run the example, do

```bash
cd <test>

python3 test_main.py \
    --config_base base_config_0.yaml \
    --config_base base_config_1.yaml \
    --config_sweep sweep_config_0.yaml \
    --config_name ./training_config.yaml

python3 test_main.py \
    --config_base base_config_0.yaml \
    --config_base base_config_1.yaml \
    --config_sweep sweep_config_0.yaml \
    --config_sweep sweep_config_1.yaml \
    --config_sweep sweep_config_2.yaml \
    --config_name ./validation_config.yaml
```

To illustrate what happens when we run the example, we use an image to show the relationship among 
all the input configuration files and the final configurations that get generated for different 
purposes. On a high level, key events are marked on the image and listed as follows (Click the image for the original resolution):

- Different sets of configuration files are used for training (1) and validation (2).
- Base configurations are merged before sweeping and embedding (3).
- Sweep configurations are merged before sweeping (4).
- A sweep variable makes different keys share the same value (5, in_chs).
- A key chain overrides a specific key-value pair (6, feature_extractor, data for validation).
- Sweep can be done using embedded configuration (7).
- An embedded configuration is first expanded (8) before merging (9) with another configuration.
- A new key-value pair can be added by merging (10).

![example](./doc/example.png)

In this example, for training, the `batch_size` is set to 32 and `in_chs` is 3. For 
validation, we use a new dataset path with a new variable `special_arg`, `batch_size` = 1, 
`in_chs` = 1, and `drop_last` = False. By having this configuration hierarchy, if the developer 
wants to change the model specification in the base configuration, e.g., the `classifier`. Then 
all future validation will automatically have this change without changing the configuration set 
up.

# Contact

Yaoyu Hu
