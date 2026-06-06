import os
import pandas as pd


class CsvLogger:
    """Buffered CSV writer. Collect rows with append(), flush once with save()."""

    def __init__(self, output_path: str, logger=None, unique: bool = True) -> None:
        self._logger = logger
        self._data = []
        self._saved = False
        self._output_path = self._unique_path(output_path) if unique else output_path

    @property
    def output_path(self) -> str:
        return self._output_path

    def __len__(self) -> int:
        return len(self._data)

    def append(self, row: dict) -> None:
        self._data.append(row)

    def save(self) -> bool:
        if self._saved:
            return False
        if not self._data:
            if self._logger:
                self._logger.warn('No data collected!')
            return False
        df = pd.DataFrame(self._data)
        df.to_csv(self._output_path, index=False)
        self._saved = True
        if self._logger:
            self._logger.info(f'Saved {len(df)} rows to {self._output_path}')
        return True

    @staticmethod
    def _unique_path(output_path: str) -> str:
        root, ext = os.path.splitext(output_path)
        counter = 1
        while os.path.exists(f"{root}_{counter}{ext}"):
            counter += 1
        return f"{root}_{counter}{ext}"
