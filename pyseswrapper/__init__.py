import numpy as np
from typing import Any
from functools import wraps

__version__ = '0.1.0'

from pathlib import Path
from .ffi import ffi, managed_dll
from .struct_bridge import (DetectorInfo, DetectorRegion, AnalyzerRegion)


def wrap_stdcall_raise(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return_value = f(*args, **kwargs)

        if isinstance(return_value, int):
            return_code = return_value
            return_value = None
        else:
            return_code, return_value = return_value

        if return_code != 0:
            raise Exception(f'FFI Error Code {return_code} in {f.__name__}')

        return return_value

    return wrapper


class SESWrapper:
    SES_PATH: str
    lib: Any

    def __init__(self, path):
        self.lib = ffi.open(path or self.SES_PATH)

    @wrap_stdcall_raise
    def initialize(self):
        return self.lib.WRP_initialize(0)

    @wrap_stdcall_raise
    def finalize(self):
        return self.lib.WRP_finalize()

    @wrap_stdcall_raise
    def reset_hardware(self):
        return self.lib.WRP_ResetHW()

    @wrap_stdcall_raise
    def test_hardware(self):
        return self.lib.WRP_TestHW()

    @wrap_stdcall_raise
    def get_property_bool(self, property_name: str, index: int = 0):
        ret_bool = ffi.new('unsigned char *')
        ret_size = ffi.new('int *')
        code = self.lib.WRP_GetPropertyBool(
            property_name.encode(), index, ret_bool, ret_size)

        return code, ret_bool[0]

    @wrap_stdcall_raise
    def get_property_int(self, property_name: str, index: int = 0):
        ret_int = ffi.new('int *')
        ret_size = ffi.new('int *')
        code = self.lib.WRP_GetPropertyBool(
            property_name.encode(), index, ret_int, ret_size)

        return code, ret_int[0]

    @wrap_stdcall_raise
    def get_property_double(self, property_name: str, index: int = 0):
        ret_double = ffi.new('double *')
        ret_size = ffi.new('int *')
        code = self.lib.WRP_GetPropertyBool(
            property_name.encode(), index, ret_double, ret_size)

        return code, ret_double[0]

    @wrap_stdcall_raise
    def set_property_double(self, property_name: str, value: float, index: int = 0):
        set_double = ffi.new('double *')
        set_double[0] = value

        ret_size = ffi.new('int *')
        return self.lib.WRP_SetPropertyDouble(property_name.encode(), index, set_double, ret_size)

    def set_pass_energy(self, pass_energy: float):
        self.set_property_double('pass_energy', pass_energy, index=-1)

    def get_pass_energy(self) -> float:
        return self.get_property_double('pass_energy')

    # and an example with structs
    @wrap_stdcall_raise
    def get_detector_info(self) -> DetectorInfo:
        p_detector_info = ffi.new('struct DetectorInfo *')
        code = self.lib.WRP_GetDetectorInfo(p_detector_info)
        detector_info = DetectorInfo()
        detector_info.from_c(p_detector_info)
        return code, detector_info

    @wrap_stdcall_raise
    def set_detector_info(self, info: DetectorInfo):
        p_detector_info = info.into_c(ffi)
        return self.lib.WRP_SetDetectorInfo(p_detector_info)

    @wrap_stdcall_raise
    def get_acquired_data(self, name: str, data_pointer, sizeof, index=0):
        return self.lib.WRP_GetAcquiredData(name.encode(), index, data_pointer, sizeof)

    def get_n_channels(self):
        p_n_channels = ffi.new('int *')
        self.get_acquired_data('acq_channels', p_n_channels, ffi.sizeof('int'))
        return p_n_channels[0]

    @wrap_stdcall_raise
    def get_spectrum(self, n_channels: int) -> np.ndarray:
        data = np.zeros(shape=(n_channels,), dtype=np.double)
        p_spectrum = ffi.cast('double *', data.ctypes.data)
        p_n_channels = ffi.new('int *')
        p_n_channels[0] = n_channels
        code = self.lib.WRP_GetAcquiredDataVectorDouble(b'acq_spectrum', 0, p_spectrum, p_n_channels)
        return code, data

    @wrap_stdcall_raise
    def start_acquisition(self):
        return self.lib.WRP_StartAcquisition()

    @wrap_stdcall_raise
    def start_acquisition(self):
        return self.lib.WRP_StartAcquisition()

    @wrap_stdcall_raise
    def continue_acquisition(self):
        return self.lib.WRP_ContinueAcquisition()

    @wrap_stdcall_raise
    def block_on_region(self):
        return self.lib.WRP_WaitForRegionReady(-1)


class DA30Analyzer:
    """
    A managed interface for the DA30 using an `SESWrapper` instance.
    You need to change the path to the wrapper library as appropriate...
    """
    path_to_wrapper: Path
    path_to_config: Path
    wrapper: SESWrapper

    def __init__(self, path_to_config, path_to_wrapper=None):
        if path_to_wrapper is None:
            path_to_wrapper = (Path.home() / 'Desktop' / 'seswrapper_2.7.7_Win64'
                               / 'seswrapper_2.7.7_Win64' / 'SESWrapper.dll')
        self.path_to_wrapper = path_to_wrapper
        self.wrapper = SESWrapper(path_to_wrapper)
        self.path_to_config = path_to_config

    def startup(self):
        self.wrapper.set_property_string('lib_working_dir', 'C:\\SES 1.4.0-r25')
        self.wrapper.set_property_string('instrument_library', self.path_to_wrapper.absolute())
        self.wrapper.initialize()
        self.wrapper.load_instrument(self.path_to_config.absolute())

    def use_transmission_mode(self):
        self.wrapper.set_property_string('element_set', 'High Pass', index=-1)
        self.wrapper.set_property_string('lens_mode', 'Transmission', index=-1)

    @property
    def detector_info(self) -> DetectorInfo:
        return self.wrapper.get_detector_info()

    @detector_info.setter
    def detector_info(self, info: DetectorInfo):
        self.wrapper.set_detector_info(info)

    @property
    def analyzer_region(self) -> AnalyzerRegion:
        return self.wrapper.get_analyzer_region()

    @analyzer_region.setter
    def analyzer_region(self, region: AnalyzerRegion):
        self.wrapper.set_analyzer_region(region)

    @property
    def pass_energy(self):
        return self.wrapper.get_pass_energy()

    @pass_energy.setter
    def pass_energy(self, pass_energy: float):
        self.wrapper.set_pass_energy(pass_energy)

    def shutdown(self):
        self.wrapper.finalize()

    def use_swept(self, low_energy: float, high_energy: float, energy_step: float, dwell_ms: int):
        self.analyzer_region = AnalyzerRegion(
            is_fixed=False, low_energy=low_energy, high_energy=high_energy,
            energy_step=energy_step, dwell_ms=dwell_ms)

    def use_fixed(self, center_energy: float, dwell_ms: int):
        self.analyzer_region = AnalyzerRegion(is_fixed=True, center_energy=center_energy, dwell_ms=dwell_ms)

    def use_full_detector(self):
        info = self.wrapper.get_detector_info()
        self.detector_region = DetectorRegion(
            0, info.n_x_chacnnels - 1, 0, info.n_y_channels - 1,
            n_slices=1, is_adc_mode=True)

    def acquire_data(self, n_iterations=1):
        self.wrapper.init_acquisition()
        n_channels_for_acquisition = self.wrapper.get_n_channels()

        for _ in range(n_iterations):
            self.wrapper.start_acquisition()
            self.wrapper.block_on_region()
            self.wrapper.continue_acquisition()

        # python list of doubles
        raw_spectrum = self.wrapper.get_spectrum(n_channels_for_acquisition)


"""
Example Usage:

analyzer = DA30Analyzer(Path(...), Path(...))
analyzer.start()

# configure
analyzer.use_transmission_mode()
analyzer.pass_energy = 5
analyzer.use_full_detector()
# <- configure to acquire around 1.5V KE with 5s acq time.
analyzer.use_fixed(center_energy=1.5, dwell_ms=5000)
   

# take data
...

# shutdown
analyzer.finalize()
"""