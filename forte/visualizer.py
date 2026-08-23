from __future__ import annotations

import numpy as np

_DEFAULT_BANDS = [
    (20, 60),
    (60, 250),
    (250, 2000),
    (2000, 6000),
    (6000, 20000),
]


class Visualizer:
    """Pure audio analysis helper producing frequency-band energy values.

    Operates on raw mono/stereo sample buffers (numpy arrays) so the future
    UI layer can feed it data and render bars without touching any UI code.
    """

    def __init__(self, bands: list[tuple[float, float]] | None = None, sample_rate: int = 44100) -> None:
        self._bands = bands if bands is not None else _DEFAULT_BANDS
        self._sample_rate = sample_rate

    def band_energies(self, samples: np.ndarray) -> list[float]:
        if samples.size == 0:
            return [0.0 for _ in self._bands]

        data = samples
        if data.ndim > 1:
            data = data.mean(axis=1)

        window = data * np.hanning(data.size)
        spectrum = np.abs(np.fft.rfft(window))
        freqs = np.fft.rfftfreq(data.size, d=1.0 / self._sample_rate)

        energies: list[float] = []
        for low, high in self._bands:
            mask = (freqs >= low) & (freqs <= high)
            band = spectrum[mask]
            energies.append(float(np.sqrt(np.mean(band ** 2))) if band.size else 0.0)
        return energies

    def normalised(self, samples: np.ndarray) -> list[float]:
        energies = self.band_energies(samples)
        peak = max(energies) if energies else 0.0
        if peak <= 0.0:
            return [0.0 for _ in energies]
        return [e / peak for e in energies]
