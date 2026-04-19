from .imodule import IModule, AsState
from jtop import jtop
import pandas as pd

class JtopLogger(IModule):
    def __init__(self, debug: bool, config: dict, logger, create_timer) -> None:
        super().__init__(debug, config, logger, create_timer)

        # ====== config ======
        self._output_path = config['output_path']
        self._jtop_timer = self._create_timer(1.0, self.jtop_timer_callback)
        self._jtop_timer.cancel()  # Start with timer stopped
        self._current_state = None
        self._jetson = None
        self._data = []
    
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
        if self._data:
            self._save_to_csv()

    # ====== internal methods ======
    def jtop_timer_callback(self) -> None:
        if self._jetson.ok():
            stats = self._jetson.stats
            self._data.append(stats)
            if self._debug:
                self._logger.info(f"Jetson Stats: {stats}")
        else:
            self._logger.error("[jtop_logger]: Error while fetching Jetson stats")

    def _save_to_csv(self) -> None:
        if not self._data:
            if self._debug:
                self._logger.warn('No data collected!')
            return

        df = pd.DataFrame(self._data)
        df.to_csv(self._output_path, index=False)
        if self._debug:
            self._logger.info(f'Saved {len(df)} rows to {self._output_path}')