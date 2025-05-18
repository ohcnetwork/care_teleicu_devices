# Care Camera Device

[![Release Status](https://img.shields.io/pypi/v/care_hello.svg)](https://pypi.python.org/pypi/care_hello)
[![Build Status](https://github.com/ohcnetwork/care_hello/actions/workflows/build.yaml/badge.svg)](https://github.com/ohcnetwork/care_hello/actions/workflows/build.yaml)

## Local Development

To develop the plug in local environment along with care, follow the steps below:

1. Go to the care root directory and clone the plugin repository:

```bash
cd care
git clone git@github.com:ohcnetwork/care_teleicu_devices.git
```

2. Add the following plug configuration to your `plug_config.py` file to enable the plugins locally:

```python
...

from plugs.manager import PlugManager
from plugs.plug import Plug

plugs = [
    Plug(
        name="gateway_device",
        package_name="/app/care_teleicu_devices", # this has to be /app/ + plugin folder name
        version="",
        configs={},
    ),
    Plug(
        name="camera_device",
        package_name="/app/care_teleicu_devices",# this has to be /app/ + plugin folder name
        version="",
        configs={},
    ),
    Plug(
        name="vitals_observation_device",
        package_name="/app/care_teleicu_devices", # this has to be /app/ + plugin folder name
        version="",
        configs={},
    ),
]

manager = PlugManager(plugs)

...
```

3. Tweak the code in plugs/manager.py to update the pip install command with the -e flag for editable installation

```python
...

subprocess.check_call(
    [sys.executable, "-m", "pip", "install", "-e", *packages] # add -e flag to install in editable mode
)

...
```

4. Install the plugins

```bash
python install_plugins.py
```

5. Rebuild the docker image and run the server

```bash
make re-build
make up
```

> [!IMPORTANT]
> Do not push these changes in a PR. These changes are only for local development.

## Production Setup

To install care camera device, you can add the plugin config in [care/plug_config.py](https://github.com/ohcnetwork/care/blob/develop/plug_config.py) as follows:

```python
...

hello_plug = [
         Plug(
             name="gateway_device",
             package_name="git+https://github.com/ohcnetwork/care_teleicu_devices",
             version="@main",
             configs={},
         ),
         Plug(
             name="camera_device",
             package_name="git+https://github.com/ohcnetwork/care_teleicu_devices",
             version="@main",
             configs={},
        ),
        Plug(
             name="vitals_observation_device",
             package_name="git+https://github.com/ohcnetwork/care_teleicu_devices",
             version="@main",
             configs={},
        ),
         ]
plugs = [hello_plug]
...
```

[Extended Docs on Plug Installation](https://care-be-docs.ohc.network/pluggable-apps/configuration.html)

## License

This project is licensed under the terms of the [MIT license](LICENSE).

---

This plugin was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) using the [ohcnetwork/care-plugin-cookiecutter](https://github.com/ohcnetwork/care-plugin-cookiecutter).

```

```
