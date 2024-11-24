import os
from ruamel.yaml import YAML
SERVICE_CONF = "service_conf.yaml"

def get_project_base_directory(*args):
    global PROJECT_BASE
    PROJECT_BASE="D:\\Rag-CKH\\"
    if PROJECT_BASE is None:
        PROJECT_BASE = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                os.pardir,
                os.pardir,
            )
        )

    if args:
        return os.path.join(PROJECT_BASE, *args)
    return PROJECT_BASE

def conf_realpath(conf_name):
    conf_path = f"{conf_name}"
    return os.path.join(get_project_base_directory(), conf_path)

def load_yaml_conf(conf_path):
    if not os.path.isabs(conf_path):
        conf_path = os.path.join(get_project_base_directory(), conf_path)
    try:
        with open(conf_path) as f:
            yaml = YAML(typ='safe', pure=True)
            return yaml.load(f)
    except Exception as e:
        raise EnvironmentError(
            "loading yaml file config from {} failed:".format(conf_path), e
        )

def get_base_config(key, default=None, conf_name=SERVICE_CONF) -> dict:
    local_config = {}
    local_path = conf_realpath(f'local.{conf_name}')
    if default is None:
        default = os.environ.get(key.upper())

    if os.path.exists(local_path):
        local_config = load_yaml_conf(local_path)
        if not isinstance(local_config, dict):
            raise ValueError(f'Invalid config file: "{local_path}".')

        if key is not None and key in local_config:
            return local_config[key]

    config_path = conf_realpath(conf_name)
    config = load_yaml_conf(config_path)

    if not isinstance(config, dict):
        raise ValueError(f'Invalid config file: "{config_path}".')

    config.update(local_config)
    return config.get(key, default) if key is not None else config

ES = get_base_config("es", {})
FLOAT_ZERO = 1e-8
PARAM_MAXDEPTH = 5

DEBUG=1
