from .imodule import IModule, AsState
from .csv_logger import CsvLogger
from diagnostic_msgs.msg import DiagnosticArray
from rclpy.qos import qos_profile_sensor_data

class HesaiTemp(IModule):
    def __init__(self, debug: bool, start_state: AsState, config: dict, node) -> None:
        super().__init__(debug, start_state, config, node)
        
        #====== config ======
        self._lidar_temp_subscriber = None
        self.lidar_temp_topic = config['lidar_temp_topic']
        self._csv = CsvLogger(config['output_path'], node.get_logger())
    
    # ====== IModule methods ======
    def _module_init(self) -> None:
        self._node.get_logger().info("[hesai_temp]: Module initialized.")

    def _module_start(self) -> None:
        self._lidar_temp_subscriber = self._node.create_subscription(DiagnosticArray, self.lidar_temp_topic, 
                                                                     self.callback, qos_profile_sensor_data)
        self._node.get_logger().info("[hesai_temp]: Module started.")

    def _module_stop(self) -> None:
        if self._lidar_temp_subscriber is not None:
            self._node.destroy_subscription(self._lidar_temp_subscriber)
        self._csv.save()
        self._node.get_logger().info("[hesai_temp]: Module stopped.")

    # ====== internal methods ======
    def callback(self, msg: DiagnosticArray) -> None:
        new_row = {'timestamp': msg.header.stamp.sec}
        for status in msg.status:
            for kv in status.values:
                new_row[kv.key] = kv.value
        self._csv.append(new_row)