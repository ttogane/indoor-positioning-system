class Airport :
  mac: str
  rssi: int

  # コンストラクタ
  def __init__(self, mac : str, rssi: int):
    self.mac = mac
    self.rssi = rssi