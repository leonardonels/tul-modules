from .imodule import IModule, AsState

from datetime import datetime
import glob
import os
import time
import can

class CanLogger(IModule):
    def __init__(self, debug: bool, start_state: AsState, config: dict, node) -> None:
        super().__init__(debug, start_state, config, node)

        # ======= config ========
        self.log_dir = config['output_path']
        self.interface = config['interface']
        self.bitrate = config['bitrate']
        self.log_name = config['log_name']
        self.use_id = config['enable_ids']


    def _module_init(self) -> None:
        if self._debug:
            self._node.get_logger().info("[can_logger]: INIT")

        if not os.path.exists(self.log_dir):
            self._node.get_logger().error(f"[can_logger]: log's path doesn't exist. Path: {self.log_dir}")
            return

        self.timestamp: datetime

        # Set pcap URI
        if self.log_dir[-1] != "/":
            self.log_dir = self.log_dir+"/"
            self._node.get_logger().warn(f"[can_logger]: invalid log dir, must end with '/', saving as {self.log_dir}")

        if "/" in self.log_name:
            self.log_name = self.log_name.split("/")[-1]
            self._node.get_logger().warn(f"[can_logger]: invalid log name, '/' not permitted, saving ad {self.log_name}")
        
        self.uri = self.log_dir + self.log_name

        if self.use_id:
            self.uri = self.uri + "__" + self.get_candump_id()

        # Set TIMESTAMP if used
        if "TIMESTAMP" in self.uri:
            self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.uri = self.uri.replace("TIMESTAMP",self.timestamp)

        os.makedirs(self.log_dir, exist_ok=True)

    
    def _module_start(self) -> None:
        if self._debug:
            self._logger.info("[can_logger]: START")

        with can.Bus(
            interface="socketcan", channel=self.interface, bitrate=self.bitrate
        ) as bus:
            logger = can.CanutilsLogWriter(self.log_dir, append=True)

            with can.Notifier(bus, [logger]):
                time.sleep(1.0)


    def _module_stop(self) -> None:
        if self._debug:
            self._logger.info("[can_logger]: STOP")
        
        self.module_stop = True

    
    def get_candump_id(self):
        found_candumps = glob.glob(f"{self.log_dir}*__*")
        max_candump_id = 0
        for candump in found_candumps:
            if os.path.isfile(candump):
                try:
                    candump_id = int(candump.split("_")[-1])
                    if candump_id > max_candump_id:
                        max_candump_id = candump_id
                except (ValueError):
                    pass
        return str(max_candump_id+1)