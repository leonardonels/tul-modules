import os
from .imodule import IModule, AsState
from jtop import jtop
import pandas as pd
from std_msgs.msg import Bool, Float32

class JtopLogger(IModule):
    def __init__(self, debug: bool, start_state: AsState, config: dict, logger, create_timer, create_publisher) -> None:
        super().__init__(debug, start_state, config, logger, create_timer, create_publisher)

        # ====== config ======
        self._jtop_timer = self._create_timer(1.0, self.jtop_timer_callback)
        self._jtop_timer.cancel()  # Start with timer stopped
        self._jetson = None
        self._df_published = False
        self._data = []
        
        self._output_path = config['output_path']
        self._check_path()

        self._publish_stats = config['publish_stats']
        if self._publish_stats:
            self._cpu_avg_publisher = self._create_publisher(Float32, config['cpu_avg_topic'][0], 1)
            self._gpu_publisher = self._create_publisher(Float32, config['gpu_topic'][0], 1)
            self._ram_publisher = self._create_publisher(Float32, config['ram_topic'][0], 1)
            self._power_publisher = self._create_publisher(Float32, config['power_topic'][0], 1)
            self._temp_publisher = self._create_publisher(Float32, config['temp_topic'][0], 1)
            self._jetson_clocks_publisher = self._create_publisher(Bool, config['jetson_clocks_topic'][0], 1)
    
    # ====== IModule methods ======
    def _module_init(self) -> None:
        try:
            self._jetson = jtop()
            self._jetson.start()
            self._logger.info("[jtop_logger]: Successfully connected to Jetson hardware monitor.")
        except Exception as e:
            self._logger.error(f"[jtop_logger]: Failed to connect to Jetson hardware monitor: {e}")

    def _module_start(self) -> None:
        self._jtop_timer.reset()    # Start logging

    def _module_stop(self) -> None:
        if self.jtop_timer_callback is not None:
            self._jtop_timer.cancel()
        if self._jetson is not None:
            self._jetson.close()
        if self._data and not self._df_published:
            self._save_to_csv()

    # ====== internal methods ======
    def jtop_timer_callback(self) -> None:
        if self._jetson.ok():
            stats = self._jetson.stats
            self._data.append(stats)
            if self._publish_stats:
                self._stats_callback(stats)
            if self._debug:
                self._logger.info(f"Jetson Stats: {stats}")
        else:
            self._logger.error("[jtop_logger]: Error while fetching Jetson stats")

    def _check_path(self) -> None:
        root, ext = os.path.splitext(self._output_path)
        counter = 1
        while os.path.exists(f"{root}_{counter}{ext}"):     # better, with room for improvement: with one read read all files with ext and number suffix, find max number and add 1 to it, instead of checking each number one by one
            counter += 1
        self._output_path = f"{root}_{counter}{ext}"

    def _save_to_csv(self) -> None:
        if not self._data:
            if self._debug:
                self._logger.warn('No data collected!')
            return

        df = pd.DataFrame(self._data)
        df.to_csv(self._output_path, index=False)
        self._df_published = True
        if self._debug:
            self._logger.info(f'Saved {len(df)} rows to {self._output_path}')

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
                self._logger.error(f"Error while publishing stats: {e}")