import argparse
import sys

# 座標を扱うクラス
class Position :
  x = 0.0
  y = 0.0

  # コンストラクタ
  def __init__(self, x : float, y: float):
    self.x = x
    self.y = y
