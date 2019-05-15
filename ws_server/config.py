import dbm.gnu


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

    def __del__(self):
        self._db.close()
