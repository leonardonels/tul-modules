from .imodule import IModule, AsState
from .csv_helper import CsvLogger
from diagnostic_msgs.msg import DiagnosticArray
from rclpy.qos import qos_profile_sensor_data

class HesaiTemp(IModule):
    def __init__(self, debug: bool, start_state: AsState, config: dict, node) -> None:
        super().__init__(debug, start_state, config, node)
        
        #====== config ======
        self._lidar_temp_subscriber = None
        self._lidar_temp_topic = config['lidar_temp_topic']
        self._csv = CsvLogger(self.__class__.__name__, config['output_path'], node.get_logger())
    
    # ====== IModule methods ======
    def _module_init(self) -> None:
        if self._start_on_state <= self._start_state:
            self._node.get_logger().info("[hesai_temp]: Module jump-initialized.")
        else:
            self._node.get_logger().info("[hesai_temp]: Module initialized.")

    def _module_start(self) -> None:
        self._lidar_temp_subscriber = self._node.create_subscription(DiagnosticArray, self._lidar_temp_topic, 
                                                                     self.callback, qos_profile_sensor_data)
        if self._start_on_state <= self._start_state:
            self._node.get_logger().info("[hesai_temp]: Module jump-started.")
        else:
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