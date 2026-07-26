# tUL node - the Ultimate Logger node

## Run
```bash
ros2 ros2 launch tul tul.launch.py
```

## Build
```bash
mkdir -p ros2_ws/src
cd ros2_ws/src

git clone https://github.com/leonardonels/tul.git --recurse-submodules

colcon build --symlink-install --packages-select tul
source install/setup.bash
```

## Add more modules
1. Create a new_module.py that extends the IModule interface.
2. Add the module inside the '/modules' folder.
3. Enjoy.

---

# IModules - the ultimate module interface
```py
from abc import ABC, abstractmethod
from enum import IntEnum

class AsState(IntEnum):
    IDLE = 0
    CHECKING = 1
    READY = 2
    DRIVE = 3
    FINISH = 4
    EMERGENCY = 5

class IModule(ABC):
    def __init__(self, debug: bool, config: dict, logger, create_timer) -> None:
        super().__init__()
        self._debug = debug
        self._config = config
        self._init_on_state =AsState(config['init_on_state'])
        self._start_on_state = AsState(config['start_on_state'])
        self._stop_on_state = AsState(config['stop_on_state'])
        self._logger = logger
        self._create_timer = create_timer

    @abstractmethod
    def _module_init(self) -> None:
        """Initialize the module."""    # not a class constructor
        pass
    
    @abstractmethod
    def _module_start(self) -> None:
        """Start the module. Called when the AS enters the start_on_state."""
        pass
    
    @abstractmethod
    def _module_stop(self) -> None:
        """Stop the module. Called when the AS enters the stop_on_state."""
        pass
    
    # ...
```

---

## Jtop module - requirements
```bash
# update and install jtop requirements
sudo apt update
sudo apt install python3-pip python3-setuptools -y

# install jtop itself (official package is too old for the latest jetsonpack versions)
sudo -v
curl -LsSf https://raw.githubusercontent.com/rbonghi/jetson_stats/master/scripts/install_jtop_torun_without_sudo.sh | bash

# add user to remove the need to 'sudo'
sudo usermod -aG jtop $USER

# jetson will be installed in a separate virtual env by design, meaning that its pythonpath is required
export PYTHONPATH="$HOME/.local/share/jtop/lib/python3.12/site-packages:$PYTHONPATH"
```
```bash
# or put it in .bashrc (the statement prevents the duplication in tmux like environments)
if [[ ":$PYTHONPATH:" != *":/home/orin/.local/share/jtop/lib/python3.12/site-packages:"* ]]; then
    export PYTHONPATH="/home/orin/.local/share/jtop/lib/python3.12/site-packages:$PYTHONPATH"
fi
```

## Candump module - requirements
```bash
# update and install python-can requirements
pip install python-can
```

# TODO:
- [ ] allow the eventual orchestrator to kill this node to - no selftdestruction
