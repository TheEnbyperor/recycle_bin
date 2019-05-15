import dbm.gnu
import struct
import enum


class CompartmentConfig:
    @enum.unique
    class CompartmentType(enum.Enum):
        LOCAL = 0
        CANBUS = 1

    _FORMAT = "<BIH"

    def __init__(self, comp_type: CompartmentType, channel: int, dev_id: int):
        self._type = comp_type
        self._channel = channel
        self._dev_id = dev_id

    @property
    def type(self):
        return self._type

    @property
    def channel(self):
        return self._channel

    @property
    def dev_id(self):
        return self._dev_id

    @classmethod
    def decode_config(cls, config: bytes):
        if len(config) != struct.calcsize(cls._FORMAT):
            return None
        comp_type, channel, dev_id = struct.unpack(cls._FORMAT, config)
        comp_type = cls.CompartmentType(comp_type)
        return cls(comp_type, channel, dev_id)


class Config:
    def __init__(self, database):
        self._db = dbm.gnu.open(database, 'cs')

    @property
    def local_authority(self):
        val = self._db.get("local_authority")
        try:
            val = val.decode()
        except UnicodeDecodeError:
            return None
        return val if len(val) != 0 else None

    @local_authority.setter
    def local_authority(self, val):
        self._db["local_authority"] = val

    def get_compartment(self, comp_id: str):
        val = self._db.get(f"comp_{comp_id}")
        try:
            val = val.decode()
        except UnicodeDecodeError:
            return None
        return CompartmentConfig.decode_config(val)

    def __del__(self):
        self._db.close()
