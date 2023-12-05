
import copy
import functools
import os
import re
import yaml

_KEY_OVERRIDE_COUNT = 0

def gather_args(args, name, force_existence=True):
    '''A very naive implementation of argument value gathering. This function gathers values of 
    a single argument name. E.g. if "--arg value1 --arg value2" is present in args, then this
    function gathers "value1" and "value2" and returns them as a list. An assertion error is raised
    if no argument with the given name is found. 
    
    This function assumes that the argument only takes a single value but there could be multiple
    instances of the same argument. The values are returned in the order they appear in args.
    
    Arguments: 
    args (list of str): the list of arguments including values. 
    name (str): the name of the argument to gather values for. 
    force_existence (bool): if True, then an assertion error is raised if no argument with the given
        is found.
    
    Returns: 
    A list of values of the argument.
    '''
    values = []
    for i, arg in enumerate(args):
        if arg == name:
            values.append( args[i+1] )
    
    assert len(values) > 0 or not force_existence, f'No {name} argument found in {args}. '
    
    return values

def remove_from_args_make_copy(args, arg_name_dict):
    '''
    arg_name_dict is a dictionary that maps the name of an argument to the number of values after
    that arguement. It assumes arguments with the same name have the same number of values. Number
    of values could be zero.
    '''
    # flags is a list of booleans. If flags[i] is False, then args[i] is removed.
    flags = []
    
    # Loop over all the arguments present in args.
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg in arg_name_dict:
            # number of arg/values to be removed including the argument itself.
            arg_count = arg_name_dict[arg] + 1
            
            for _ in range( arg_count ):
                flags.append(False)
            
            i += arg_count
        else:
            # Keep this arg.
            flags.append(True)
            i += 1
    
    # Only keep the arguments with flag set to True.    
    return [ arg for arg, flag in zip(args, flags) if flag ]

def separate_dict_key_chain_prefix(s):
    '''A prefixe configuration filename could be in the following format:
    
    key0.key1@/path/to/config.yaml
    
    This function returns "key0.key1" and "/path/to/config.yaml" as a tuple of strings. If no prefix
    is found, then None is returned as the prefix and the path string is returned as the second
    element of the tuple.
    
    Arguments:
    s (str): the string to be parsed.
    
    Returns:
    A tuple of strings. The first element is the prefix (will be None if no prefix found) and the
    second element is the path string.
    '''
    m = re.search(r'^([\w\d\.]+)\@.+\.yaml$', s)
    if m:
        return m.group(1), s[len(m.group(1))+1:]
    else:
        return None, s

def parse_yaml_filename(fn):
    '''Check if fn is ending with ".yaml" or ".yaml@xxx@yyy". Where the "@xxx" suffix is optional and
       "xxx" must not be ".yaml".
       
       If the test passes, then the function returns the valid filename after removing the
       "@xxx@yyy" suffix. All the detected suffixes will be returned in a seprate list.
       
       If the test fails, then this function returns None and []. 
    '''
    
    lower_fn = fn.lower()
    
    # Check bare ".yaml" suffix.
    if lower_fn.endswith(".yaml"):
        return fn, []
    
    # Check ".yaml@xxx@yyy" suffix.
    m = re.search(r'(.+\.yaml)(@.+)', lower_fn)
    
    if m:
        return m[1], m[2].split('@')[1:]
    
    return None, []

def substitute_config_yaml(d):
    '''Go through dictionary d and replace any value that is a string and ends with ".yaml" with the
    content read from the yaml file. If the yaml file also contains embedded yaml file names, then
    all instances of yaml filenames will be recursively read.
    
    Note: This function modifies d in-place.
    
    Arguments:
    d (dict): a dictionary represent a configuration. Will be modified in-place.
    '''
    for k, v in d.items():    
        if isinstance(v, str):
            fn, _ = parse_yaml_filename(v)
            if fn is not None:
                d[k] = read_config(fn, recursive=True)
        elif isinstance(v, dict):
            substitute_config_yaml(v)

def get_value_from_key_chain(d, key_chain):
    '''Get the value of a key chain from a dictionary.
    
    Arguments:
    d (dict): the dictionary to be searched.
    key_chain (list of str): the key chain to be searched.
    
    Returns:
    The value of the key chain in the dictionary. If the key chain is not found, then a ValueError
    is raised.
    '''
    flag = True # Wil be set to False if the key chain is broken. 
    value = d
    for i, k in enumerate(key_chain):
        if k in value:
            value = value[k]
        else:
            flag = False
            break
    
    if flag:
        return value
    
    # The key chain is broken.
    key_chain = key_chain[:i]
    
    raise ValueError(
        f'Key chain broken at {key_chain}. \n'
        f'Where the available keys at the point of break are: {value.keys()}. ')

def read_config(fn, recursive=False):
    '''Complex config file reader.
    
    This reader deals with file names that could have a prefix in the form of 
    "key0.key1@config.yaml". When this happens, the reader will first read the yaml file and then
    get the value of config[key0][key1] and return it. When there is not a prefix (not a learding 
    string that ends with "@"), then the config file is read as usual.
    
    When recursive is True, then this reader recursively treats any value that is a string and 
    ends with ".yaml" as a configuration file and uses the content of that file to replace the yaml
    filename string. The above prefix rule also applies.
    
    Arguments:
    fn (str): the filename of the config file.
    
    Returns:
    A dictionary that represnet the content of the config file.
    '''
    # Check if there is a prefix in the filename.
    prefix, fn = separate_dict_key_chain_prefix(fn)
    
    with open(fn, "r") as fp:
        param_dict = yaml.load(fp, Loader=yaml.FullLoader)

    if recursive:
        substitute_config_yaml(param_dict)
                
    # If we need to get the special value from the key chain.
    if prefix is not None:
        key_chain = prefix.split(".")
        param_dict = get_value_from_key_chain(param_dict, key_chain)
    
    return param_dict

def merge_dicts( d_to, d_from, path=[] ):
    '''
    Inspired by https://gist.github.com/angstwad/bf22d1822c38a92ec0a9 and
    https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries?page=1&tab=scoredesc#tab-top
    
    Merge from d_from to d_to. If there is a key conflict, then the values are merged in the
    following logic:
    - If either of the values is a string ending with ".yaml", then the value will be replaced by
      reading the yaml file without recursive parsing.
    - If either of the values is a string ending with ".yaml@deferred_merge", then the yaml file
      will NOT be read. The filename is used as normal string.
    - If both values (after potential YAML file parsing) are dictionaries, then the values will be
      merged. Otherwise (*), d_from's value will be used and a message will be printed to the
      terminal.
    
    Note: d_to is updated in-place and the function also returns the final, modified d_to.
    Note: every time an override (*) happens, there will be a counter number associated with the
        message that gets printed. This counter value is for debugging purpose. The developer can
        then drop breakpoints conditioned on the counter value.
    
    path is a list of strings to show the key chain if an override happens.
    '''
    
    global _KEY_OVERRIDE_COUNT
    
    for key, value in d_from.items():
        if key in d_to: 
            if isinstance(value, str):
                fn, suffixes = parse_yaml_filename(value)
                if fn is not None and 'deferred_merge' not in suffixes:
                    value = read_config(fn, recursive=False)
            
            value_to_ori = d_to[key]
            if isinstance(value_to_ori, str) and isinstance(value, dict):
                fn, _ = parse_yaml_filename(value_to_ori)
                if fn is not None:
                    d_to[key] = read_config(value_to_ori, recursive=False)
            
            if isinstance(value, dict) and isinstance(d_to[key], dict):
                merge_dicts(d_to[key], value, path + [str(key)])
            else:
                print(f'Key override ({_KEY_OVERRIDE_COUNT}) at {".".join(path + [str(key)])}. ')
                d_to[key] = value
                _KEY_OVERRIDE_COUNT += 1
        else:    
            d_to[key] = value
            
    return d_to

def construct_dict_from_dot_notation(key, value):
    '''key is a key chain string in the form "a.b.c". This function will return a dictionary with 
    the following structure:
    {
        "a": {
            "b": {
                "c": value
            }
        }
    }
    '''
    keys = key.split(".")
    keys.reverse()
    v = value
    for k in keys:
        d = dict()
        d[k] = v
        v = d
    return d

def substitute_sweep_at(d, sweep_at_dict, prefix='sweep@', path=[]):
    '''This function takes two dicts:
    d: a dictionary that contains values as strings starting with "sweep@". This could happen at any
        level (sub-key) of d. 
    sweep_at_dict: a dictionary that maps the string "sweep@xxx" to the actual value that need to be
        sweeped.
    
    This function does the sweep recursively and in-place.
    
    Note: Currently if a sweeped value is a string ending with ".yaml", then this yaml file will NOT
    be parsed in a recursive way. Recursive parsing is done by the read_config() function, WIHTOUT
    sweeping. So sweep without yaml filenames and do it at the end of configuration file parsing.
    
    path is a list of strings to show the key chain if sweep happens.
    '''
    for k, v in d.items():
        if isinstance(v, str) and v.startswith(prefix):
            d[k] = sweep_at_dict[v]
            print(f'Value sweeped at {".".join(path + [str(k)])} with {v}. ')
        elif isinstance(v, dict):
            substitute_sweep_at(v, sweep_at_dict, prefix=prefix, path=path + [str(k)])

def read_and_merge_config_files(config_paths):
    '''This function reads all the files specified by configs_paths and merge them together.
    '''
    config_list = [ read_config(p) for p in config_paths ]
    return functools.reduce(merge_dicts, config_list)

def read_and_merge_base_config_files(argv, arg_config_name):
    '''This function search for all the values after the argument arg_config_name in argv. Then it
    reads all the configuration files specified by those values and merge them into a single
    dictionary. Recursive YAML file parsing does NOT happen.
    '''
    config_paths = gather_args(argv, arg_config_name, force_existence=True)
    return read_and_merge_config_files(config_paths)

def read_and_merge_sweep_config_files(argv, arg_config_name):
    '''This function search for all the values after the argument arg_config_name in argv. Then it
    reads all the configuration files specified by those values and merge them into a single
    dictionary. Recursive YAML file parsing does NOT happen.
    
    Then sweep entries and key chains are splited into two separate dictionaries.
    
    Note: if arg_config_name is not found in argv, then this function returns two empty dictionaries.
    '''
    sweep_paths = gather_args(argv, arg_config_name, force_existence=False)
    if len(sweep_paths) == 0:
        return dict(), dict()
    
    config_sweep = read_and_merge_config_files(sweep_paths)
    
    # Expand the key chains in config_sweep.
    config_sweep_as_list_of_dicts = [ 
        construct_dict_from_dot_notation(k, v) for k, v in config_sweep.items() ]
    config_sweep = functools.reduce(merge_dicts, config_sweep_as_list_of_dicts)
    
    # Split the sweep@ entries in config_sweep.
    sweep_at_entries = dict()
    for k, v in config_sweep.items():
        if k.startswith("sweep@"):
            sweep_at_entries[k] = v
    
    # Remove the sweep@ entries from config_sweep.
    for k in sweep_at_entries.keys():
        config_sweep.pop(k)
        
    return config_sweep, sweep_at_entries

def construct_config_on_filesystem(
        argv,
        top_level_single_key=None,
        name_config_base='--config_base', 
        name_config_sweep='--config_sweep',
        name_config_name='--config_name',
        **kwargs ):
    '''
    This function reads the values in argv. It tries to construct a new configuration by merging
    multiple configuration files. Then the newly merged configuration will be saved to the
    filesystem as specified by the name_config_name argument.
    
    It is assumed that there is at least a name_config_base argument and/or a name_config_sweep
    argument. If not, then this function does nothing and returns None. If the condition is met,
    then this function tries to combine all the name_config_sweep into a single dictionary and all
    the name_config_base will be combined into a single dictionary. Then the sweep dictionary will
    override the values in the base dictionary. The final dictionary will be saved as a yaml file.
    The name of the yaml file will be determined by the name_config_name argument, which is assumed
    to exist.
    
    While merging different configuration files, this function also performs recursive yaml file
    reading and value sweeping. Refer to the read_config() and substitute_sweep_at() functions for
    more details. Here is an example of a sweep configuration file:
    
    === Example config_sweep.yaml ===
    sweep@exp_name: "CR_EV004"
    sweep@main_dataset_print_img_freq: 1
    sweep@main_dataset_step_size: 1

    fit.data: "/working_root/config/ev_main_dataset.yaml"
    fit.model.init_args.val_loader_names: "/working_root/config/ev_data_dirs.yaml"
    fit.model.init_args.val_offline_flag: true
    fit.model.init_args.val_custom_step: true
    fit.trainer.callbacks: "callbacks@/working_root/config/ev_trainer_callbacks.yaml"
    === End of example config_sweep.yaml ===
    
    Here a "sweep@xxx" entry defines a sweeped value. Then a single row of key chain following by a
    value will be used for overriding a base configuration. E.g. fit.data:
    "/working_root/config/ev_main_dataset.yaml". For such an key chain override, the user could
    specify a YAML file. When a YAML file is specified, then the content of the YAML file will be
    recursively parsed and taken as the value of this key chain. A prefix is allowed to be place in
    front of a YAML filename. E.g. "callbacks@/working_root/config/ev_trainer_callbacks.yaml", which
    means that after recursively parsing the YAML file, the value of the "callbacks" key chain will
    be used instead of the entire yaml file content.
    
    What will happen is that all the sweep configuration files specified by the name_config_sweep
    arguments will be first merged into a single sweep configuration without yaml file reading and
    sweeping, only overriding happens during this stage. Then the newly merged sweep configuration
    will be used to override the base configuration, which is generated by merging all
    name_config_base arguments. This time, embedded yaml filenames are recursively parsed. Finally,
    the sweeped values are substituted as specified by the (merged) sweep@ entries.
    
    Arguments:
    argv (list of str): the list of arguments to be parsed.
    top_level_single_key (str): if not None, then the top level key of the merged configuration will
        be used as the outout configuration and get saved to the filesystem.
    name_config_base (str): the name of the argument that specifies the base configuration file.
    name_config_sweep (str): the name of the argument that specifies the sweep configuration file.
    name_config_name (str): the name of the argument that specifies the file name of the output.
    kwargs (dict): additional key-value pairs to be added to the final configuration after handling
        top_level_single_key.
    
    Returns:
    The path to the generated yaml file. 
    '''
    
    # Gather all the name_config_base arguments.
    config_base = read_and_merge_base_config_files(argv, name_config_base)
    
    # Merge all the name_config_sweep arguments.
    config_sweep, sweep_at_entries = read_and_merge_sweep_config_files(argv, name_config_sweep)
    
    # Merge the base and sweep dictionaries.
    config = copy.deepcopy(config_base)
    merge_dicts(config, config_sweep)
    
    # Perform YAML file substitution.
    substitute_config_yaml(config)
    
    # Perform sweep@ substitution.
    substitute_sweep_at(config, sweep_at_entries)
    
    # Get the top level single key.
    if top_level_single_key is not None:
        config = config[top_level_single_key]
    
    # Add additional key-value pairs.
    for k, v in kwargs.items():
        config[k] = v
    
    # Save the config to a file.
    config_names = gather_args(argv, name_config_name, force_existence=True)
    
    if len(config_names) > 1:
        error_msg = f'Only one {name_config_name} argument is allowed. There are {len(config_names)} found: \n'
        for config_name in config_names:
            error_msg += f'\t{config_name}\n'
        raise ValueError(error_msg)
    
    config_name = config_names[0]
    
    os.makedirs(os.path.dirname(config_name), exist_ok=True)
    with open(config_name, "w") as fp:
        yaml.dump(config, fp)
        
    return config_name
    