"""Windows: un file audio (MP3, M4A, WMA, ...) in campioni PCM a 16 bit, con Media
Foundation, il decodificatore che Windows usa per i suoi lettori. Nessuna libreria in
più: le interfacce COM si chiamano con ctypes (vedi mfreadwrite.h e mfobjects.h).

Le edizioni "N" di Windows senza Media Feature Pack non hanno Media Foundation: lì
decode() dà errore e GlucoBar usa i suoi suoni."""

import ctypes
from ctypes import POINTER, byref, c_long, c_uint32, c_uint64, c_void_p, wintypes

HRESULT = c_long
MF_VERSION = 0x00020070
FIRST_AUDIO_STREAM = 0xFFFFFFFD
ALL_STREAMS = 0xFFFFFFFE
END_OF_STREAM = 0x2
TYPE_CHANGED = 0x20   # il decodificatore ha cambiato formato (es. AAC a 22 kHz)


class GUID(ctypes.Structure):
    _fields_ = [("Data1", c_uint32), ("Data2", ctypes.c_uint16), ("Data3", ctypes.c_uint16),
                ("Data4", ctypes.c_ubyte * 8)]

    def __init__(self, text):
        import uuid
        u = uuid.UUID(text)
        super().__init__(u.time_low, u.time_mid, u.time_hi_version,
                         (ctypes.c_ubyte * 8)(*u.bytes[8:]))


MT_MAJOR_TYPE = GUID("48eba18e-f8c9-4687-bf11-0a74c9f96a8f")
MT_SUBTYPE = GUID("f7e34c9a-42e8-4714-b74b-cb29d72c35e5")
MEDIATYPE_AUDIO = GUID("73647561-0000-0010-8000-00aa00389b71")
AUDIOFORMAT_PCM = GUID("00000001-0000-0010-8000-00aa00389b71")
MT_AUDIO_CHANNELS = GUID("37e48bf5-645e-4c5b-89de-ada9e29b696a")
MT_AUDIO_RATE = GUID("5faeeae7-0290-4c31-9e8a-c534f68d9dba")
MT_AUDIO_BITS = GUID("f2deb57f-40fa-4764-aa33-ed4f2d1ff669")

# posizione dei metodi nella tabella delle interfacce
RELEASE = 2
ATTR_GET_UINT32, ATTR_SET_UINT32, ATTR_SET_GUID = 7, 21, 24
READER_SET_SELECTION, READER_GET_TYPE, READER_SET_TYPE, READER_READ = 4, 6, 7, 9
SAMPLE_CONTIGUOUS = 41
BUFFER_LOCK, BUFFER_UNLOCK = 3, 4


def _call(obj, index, argtypes, *args):
    vtable = ctypes.cast(obj, POINTER(POINTER(c_void_p))).contents
    method = ctypes.WINFUNCTYPE(HRESULT, c_void_p, *argtypes)(vtable[index])
    hr = method(obj, *args)
    if hr < 0:
        raise OSError(f"Media Foundation: 0x{hr & 0xFFFFFFFF:08X}")
    return hr


def _release(obj):
    if obj:
        _call(obj, RELEASE, [])


def decode(path, max_seconds=60):
    """(canali, campioni al secondo, byte PCM a 16 bit) del file."""
    ole32 = ctypes.windll.ole32
    mfplat = ctypes.windll.mfplat
    mfreadwrite = ctypes.windll.mfreadwrite
    # COM per questo thread (se c'è già, in un altro modo, va bene lo stesso)
    com = ole32.CoInitializeEx(None, 0)
    _check(mfplat.MFStartup(MF_VERSION, 0))
    reader = c_void_p()
    wanted = c_void_p()
    try:
        _check(mfreadwrite.MFCreateSourceReaderFromURL(wintypes.LPCWSTR(path), None,
                                                       byref(reader)))
        _call(reader, READER_SET_SELECTION, [c_uint32, wintypes.BOOL], ALL_STREAMS, False)
        _call(reader, READER_SET_SELECTION, [c_uint32, wintypes.BOOL], FIRST_AUDIO_STREAM, True)
        _check(mfplat.MFCreateMediaType(byref(wanted)))
        guid_args = [POINTER(GUID), POINTER(GUID)]
        _call(wanted, ATTR_SET_GUID, guid_args, byref(MT_MAJOR_TYPE), byref(MEDIATYPE_AUDIO))
        _call(wanted, ATTR_SET_GUID, guid_args, byref(MT_SUBTYPE), byref(AUDIOFORMAT_PCM))
        _call(wanted, ATTR_SET_UINT32, [POINTER(GUID), c_uint32], byref(MT_AUDIO_BITS), 16)
        _call(reader, READER_SET_TYPE, [c_uint32, c_void_p, c_void_p],
              FIRST_AUDIO_STREAM, None, wanted)
        channels, rate = _format(reader)
        data = bytearray()
        while len(data) < max_seconds * rate * channels * 2:
            index, flags, stamp, sample = c_uint32(), c_uint32(), c_uint64(), c_void_p()
            _call(reader, READER_READ, [c_uint32, c_uint32, POINTER(c_uint32), POINTER(c_uint32),
                                        POINTER(c_uint64), POINTER(c_void_p)],
                  FIRST_AUDIO_STREAM, 0, byref(index), byref(flags), byref(stamp), byref(sample))
            if flags.value & TYPE_CHANGED:
                # il formato vero arriva col primo pezzo; se cambia dopo (raro), i pezzi
                # nel formato di prima non si possono mescolare ai nuovi
                new = _format(reader)
                if new != (channels, rate):
                    data.clear()
                channels, rate = new
            if sample:
                data += _sample_bytes(sample)
                _release(sample)
            if flags.value & END_OF_STREAM:
                break
        if not data:
            raise OSError("Media Foundation: nessun suono nel file")
        return channels, rate, bytes(data[:max_seconds * rate * channels * 2])
    finally:
        for obj in (wanted, reader):
            _release(obj)
        mfplat.MFShutdown()
        if com >= 0:
            ole32.CoUninitialize()


def _format(reader):
    """(canali, campioni al secondo) che il lettore restituisce adesso, a 16 bit."""
    actual = c_void_p()
    _call(reader, READER_GET_TYPE, [c_uint32, POINTER(c_void_p)],
          FIRST_AUDIO_STREAM, byref(actual))
    try:
        values = []
        for guid in (MT_AUDIO_CHANNELS, MT_AUDIO_RATE, MT_AUDIO_BITS):
            out = c_uint32()
            _call(actual, ATTR_GET_UINT32, [POINTER(GUID), POINTER(c_uint32)],
                  byref(guid), byref(out))
            values.append(out.value)
    finally:
        _release(actual)
    if values[2] != 16:
        raise OSError(f"Media Foundation: {values[2]} bit")
    return values[0], values[1]


def _sample_bytes(sample):
    buffer = c_void_p()
    _call(sample, SAMPLE_CONTIGUOUS, [POINTER(c_void_p)], byref(buffer))
    try:
        ptr, length = c_void_p(), c_uint32()
        _call(buffer, BUFFER_LOCK, [POINTER(c_void_p), c_void_p, POINTER(c_uint32)],
              byref(ptr), None, byref(length))
        try:
            return ctypes.string_at(ptr, length.value)
        finally:
            _call(buffer, BUFFER_UNLOCK, [])
    finally:
        _release(buffer)


def _check(hr):
    if hr < 0:
        raise OSError(f"Media Foundation: 0x{hr & 0xFFFFFFFF:08X}")


def convert(pairs):
    """[sorgente, wav, sorgente, wav, ...] -> i WAV; 0 se sono riusciti tutti. Gira in un
    processo a parte (vedi sound.decode_all)."""
    import os
    import wave
    failed = 0
    for src, out in zip(pairs[::2], pairs[1::2]):
        try:
            channels, rate, frames = decode(src)
            with wave.open(out + ".tmp", "wb") as f:
                f.setnchannels(channels)
                f.setsampwidth(2)
                f.setframerate(rate)
                f.writeframes(frames)
            os.replace(out + ".tmp", out)
        except Exception as e:
            failed += 1
            print(f"{os.path.basename(src)}: {e}", file=__import__("sys").stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(convert(sys.argv[1:]))
