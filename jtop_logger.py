from .imodule import IModule, AsState
from .csv_logger import CsvLogger
from jtop import jtop
from rclpy.node import Node
from std_msgs.msg import Bool, Float32

class JtopLogger(IModule):
    def __init__(self, debug: bool, start_state: AsState, config: dict, node: Node) -> None:
        super().__init__(debug, start_state, config, node)

        # ====== config ======
        self._jtop_timer = self._node.create_timer(1.0, self.jtop_timer_callback)
        self._jtop_timer.cancel()  # Start with timer stopped
        self._jetson = None
        self._csv = CsvLogger(config['output_path'], node.get_logger())

        self._publish_stats = config['publish_stats']
        if self._publish_stats:
            self._cpu_avg_publisher = self._node.create_publisher(Float32, config['out_topic_prefix'] + '/cpu_avg_stats', 1)
            self._gpu_publisher = self._node.create_publisher(Float32, config['out_topic_prefix'] + '/gpu_stats', 1)
            self._ram_publisher = self._node.create_publisher(Float32, config['out_topic_prefix'] + '/ram_stats', 1)
            self._power_publisher = self._node.create_publisher(Float32, config['out_topic_prefix'] + '/power_stats', 1)
            self._temp_publisher = self._node.create_publisher(Float32, config['out_topic_prefix'] + '/temp_stats', 1)
            self._jetson_clocks_publisher = self._node.create_publisher(Bool, config['out_topic_prefix'] + '/jetson_clocks_stats', 1)
    
    
    # ====== IModule methods ======
    def _module_init(self) -> None:
        try:
            self._jetson = jtop()
            self._jetson.start()
            if self._start_on_state <= self._start_state:
                self._node.get_logger().info("[jtop_logger]: Successfully connected to Jetson hardware monitor. Module jump-initialized.")
            else:
                self._node.get_logger().info("[jtop_logger]: Successfully connected to Jetson hardware monitor.")
        except Exception as e:
            self._node.get_logger().error(f"[jtop_logger]: Failed to connect to Jetson hardware monitor: {e}")

    def _module_start(self) -> None:
        self._jtop_timer.reset()    # Start logging
        if self._start_on_state <= self._start_state:
            self._node.get_logger().info("[jtop_logger]: Module jump-started.")
        else:
            self._node.get_logger().info("[jtop_logger]: Module started.")

    def _module_stop(self) -> None:
        if self.jtop_timer_callback is not None:
            self._jtop_timer.cancel()
        if self._jetson is not None:
            self._jetson.close()
        self._csv.save()


    # ====== internal methods ======
    def jtop_timer_callback(self) -> None:
        if self._jetson.ok():
            stats = self._jetson.stats
            self._csv.append(stats)
            if self._publish_stats:
                self._stats_callback(stats)
            if self._debug:
                self._node.get_logger().info(f"Jetson Stats: {stats}")
        else:
            self._node.get_logger().error("[jtop_logger]: Error while fetching Jetson stats")

    def _stats_callback(self, stats: dict) -> None:
        if self._publish_stats:
            try:
                cpu_keys = [k for k in stats if k.startswith('CPU')]
                cpu_avg=Float32(data = sum(stats[k] for k in cpu_keys) / len(cpu_keys))
                self._cpu_avg_publisher.publish(cpu_avg)

                self._gpu_publisher.publish(Float32(data=stats['GPU']))
                self._ram_publisher.publish(Float32(data=stats['RAM']))
                self._power_publisher.publish(Float32(data=stats['Power TOT'] /1000))
                self._temp_publisher.publish(Float32(data=stats['Temp soc0']))
                self._jetson_clocks_publisher.publish(Bool(data=stats['jetson_clocks'] == 'ON'))
            except Exception as e:
                self._node.get_logger().error(f"Error while publishing stats: {e}")