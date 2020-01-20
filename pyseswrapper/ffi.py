import warnings
from pathlib import Path
from cffi import FFI

__all__ = ('ffi', 'managed_dll',)

headers_path = Path(__file__).parent / 'headers' / 'seswrapper.h'

ffi = FFI()

with open(str(headers_path)) as f:
    ffi.cdef(f.read())


class ManagedDLL:
    dll = None
    load_path: str = None

    def open(self, path):
        path = str(path)
        if self.dll is None:
            self.dll = ffi.dlopen(path)
            self.load_path = path
        else:
            if self.load_path != path:
                warnings.warn('Requesting SESWrapper from a different location after initial load,'
                              'returning the original cached wrapper.')

            return self.dll

managed_dll = ManagedDLL()