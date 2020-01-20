from dataclasses import make_dataclass, dataclass
from typing import Union, Tuple, Any, Type

__all__ = (
    # Utilities
    'StructField',
    'wrap_struct_dataclass',

    # Mapped structs for SESWrapper
    'DetectorInfo',
    'DetectorRegion',
    'AnalyzerRegion'
)


@dataclass
class StructField:
    pyname: str
    pytype: type

    cname: str
    ctype: str
    pydefault: Any = None


class CBridge:
    """
    I am only for type hinting.
    """
    def into_c(self):
        raise NotImplementedError()

    def from_c(self, c_struct_pointer: Any) -> Type['CBridge']:
        raise NotImplementedError()


def wrap_struct_dataclass(struct_name, fields, name=None) -> Type[CBridge]:
    """
    Works best with primitive types for now
    """

    if name is None:
        name = struct_name

    MAP_FIELDS = {
        'int': int,
        'float': float,
        'double': float,
        'char': int,
    }

    MAP_PY_DEFAULTS = {
        int: 0,
        float: 0.,
        bool: False,
        str: '',
    }

    def full_field(f: Union[StructField, Tuple[str, str]]):
        if isinstance(f, StructField):
            return f
        else:
            name, ctype = f
            return StructField(pyname=name, cname=name, ctype=ctype, pytype=MAP_FIELDS[ctype])

    full_fields = {ff.pyname: ff for ff in [full_field(f) for f in fields]}

    def into_c(self, ffi):
        pointer = ffi.new(f'struct {struct_name} *')

        for field_name, field in self._cfields_.items():
            setattr(pointer, field.cname, getattr(self, field.pyname))

        return pointer

    def from_c(self, c_pointer):
        # populate self from fields...
        for field_name, field in self._cfields_.items():
            # this might need adjusting if more complex types are required
            setattr(self, field.pyname, field.pytype(getattr(
                c_pointer, field.cname)))

    def unwrap_field(f: StructField):
        return f.pyname, f.pytype, f.pydefault

    return make_dataclass(
        name,
        [[unwrap_field(full_field(f)) for f in fields]],
        namespace={
            'into_c': into_c,
            'from_c': from_c,
            '_cfields_': full_fields,
        })


DetectorInfo = wrap_struct_dataclass('DetectorInfo', [
    StructField('is_timer_controlled', bool, 'timerControlled_', 'unsigned char'),
    StructField('n_x_channels', int, 'xChannels_', 'int'),
    StructField('n_y_channels', int, 'yChannels_', 'int'),
    StructField('max_slices', int, 'maxSlices_', 'int'),
    StructField('max_channels', int, 'maxChannels_', 'int'),
    StructField('frame_rate', int, 'frameRate_', 'int'),
    StructField('is_adc_present', bool, 'adcPresent_', 'unsigned char'),
    StructField('is_disc_present', bool, 'discPresent_', 'unsigned char'),
])

DetectorRegion = wrap_struct_dataclass('DetectorRegion', [
    StructField('first_x_channel', int, 'firstXChannel_', 'int'),
    StructField('last_x_channel', int, 'lastXChannel_', 'int'),
    StructField('first_y_channel', int, 'firstYChannel_', 'int'),
    StructField('last_y_channel', int, 'lastYChannel_', 'int'),
    StructField('n_slices', int, 'slices_', 'int'),
    StructField('is_adc_mode', bool, 'adcMode_', 'unsigned char'),
])

AnalyzerRegion = wrap_struct_dataclass('AnalyzerRegion', [
    StructField('is_fixed', bool, 'fixed_', 'unsigned char'),
    StructField('high_energy', float, 'highEnergy_', 'double'),
    StructField('low_energy', float, 'lowEnergy_', 'double'),
    StructField('center_energy', float, 'centerEnergy_', 'double'),
    StructField('energy_step', float, 'energyStep_', 'double'),
    StructField('dwell_ms', int, 'dwellTime_', 'int'),
])
