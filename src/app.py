from typing import List
from modules.airport import Airport
from modules.position import Position
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import subprocess
import xml.etree.ElementTree as ET

# 電波強度減衰定数(理想値: 20)
_n = 28

# 以下より計算できる
# P : 送信電力
# D : n[m]
# Dの地点の電波強度　PD = P / 4πD
# D =1, RSSI = 10log10(P / 4π)
_rssi0 = -32

# wifiの電波強度を取得するコマンド
_airport = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'

# 室内にあるAPの座標情報
_ap = {
  'xx:xx:xx:xx:xx:xx': Position(6.0, 6.0),
  'yy:yy:yy:yy:yy:yy': Position(15.0, 5.7),
  'zz:zz:zz:zz:zz:zz': Position(10, 10),
}

# 描画する画像に対しての座標の倍率
_expand_rate = 100

# RSSIからアクセスポイントまでの距離を予測する。
def predict_distance_from_rssi(rssi: int) -> float:
  return 10**-((rssi - _rssi0)/ _n)

# 室内での端末の座標算出する
# [参考資料]
# https://ipsj.ixsq.nii.ac.jp/ej/?action=repository_action_common_download&item_id=184479&item_no=1&attribute_id=1&file_no=1
# http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.684.6710&rep=rep1&type=pdf
def get_device_indoor_position(airports: List[Airport]) -> Position:

  # macアドレスから検出された3つのアクセスポイントの座標を取得する
  _ap1 = _ap[airports[0].mac]
  _ap2 = _ap[airports[1].mac]
  _ap3 = _ap[airports[2].mac]
  print('_ap1 = x: {0} y:{1}\n_ap2 = x: {2} y:{3}\n_ap3 = x: {4} y:{5}\n'.format(_ap1.x, _ap1.y, _ap2.x, _ap2.y, _ap3.x, _ap3.y))

  # 検出したAPのrssiから距離を計算する
  _r1 = predict_distance_from_rssi(airports[0].rssi)
  _r2 = predict_distance_from_rssi(airports[1].rssi)
  _r3 = predict_distance_from_rssi(airports[2].rssi)
  print('r1: {0}\nr2: {1}\nr3: {2}\n'.format(_r1, _r2, _r3))

  # パラメータを計算する
  va = ((_r2**2 - _r3**2) - (_ap2.x**2 - _ap3.x**2) - (_ap2.y**2 - _ap3.y**2))/2
  vb = ((_r2**2 - _r1**2) - (_ap2.x**2 - _ap1.x**2) - (_ap2.y**2 - _ap1.y**2))/2
  print('va: {0}\nvb: {1}\n'.format(va, vb))
  
  # 座標を算出する
  y = (vb * (_ap3.x - _ap2.x) - va * (_ap1.x - _ap2.x)) / ((_ap1.y - _ap2.y) * (_ap3.x - _ap2.x) - (_ap3.y - _ap2.y) * (_ap1.x - _ap2.x))
  x = (va - y * (_ap3.y - _ap2.y)) / (_ap3.x - _ap2.x)

  return Position(x, y)

# 間取り図に位置を描画する
# 赤: WIFIルーターの位置
# 青: 推定された位置座標
def draw_position(position: Position):

  ap_size = 50
  ap_color = (233,56,78)

  device_size = 100
  device_color = (78,56,233)

  im = Image.open('src/image/floor_plan.png')
  draw = ImageDraw.Draw(im)

  # APの位置を描画
  for key in _ap.keys():
    x = _ap[key].x * _expand_rate
    y = _ap[key].y * _expand_rate
    xy = (x, y, x + ap_size, y + ap_size)
    draw.ellipse(xy, fill=(ap_color))

  # deviceの位置を描画
  xd = position.x * _expand_rate
  yd = position.y * _expand_rate
  xy_d =  (xd, yd, xd + device_size, yd + device_size)
  draw.ellipse(xy_d, fill=device_color)

  plt.imshow(im)
  plt.show()



def main():

  # macが接続可能なwifiをXMLとして取得する
  res = subprocess.run('{0} {1} {2}'.format(_airport, '-s', '-x'), encoding='utf-8', stdout=subprocess.PIPE, shell=True)# .check_output(_airport, shell=True)
  content_xml = res.stdout
  
  # xmlを解析
  root = ET.fromstring(content_xml)
  child = root.find('array').findall('dict')
  
  # 計測に利用するAPのリストを作成する(= 強度の強い順)
  # mac => c.findall('string')[0].text
  # ssid=> c.findall('string')[1].text
  # rssi=> int(c.findall('integer')[7].text)
  airport = [ Airport(c.findall('string')[0].text, int(c.findall('integer')[7].text)) for c in reversed(child) if c.findall('string')[0].text in _ap.keys() ]

  # 位置のわかるAPが３つ以上見つからなかったらエラーとして処理
  if len(airport) <= 2:
    raise Exception('APが必要数検出できませんでした')

  # 端末の位置を計測する (= 使うのはAP３つ)
  position = get_device_indoor_position(airport[:3])
  print('x: {0}\ny: {1}\n'.format(position.x, position.y))

  # 間取り上に描画
  draw_position(position)


''' メイン '''
if __name__ == '__main__':
  main()