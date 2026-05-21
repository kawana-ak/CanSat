"""
BNO055のキャリブレーション完了後に
方位角(heading)を取得するサンプル

Author: 川名
Environment:
    Raspberry Pi Pico
    BNO055
"""
from bno055 import BNO055
from machine import I2C , Pin
import time

class BNO055DEMO:
    
    #キャリブレーションの値を初期化
    sys = None
    gyro = None
    accel = None
    mag = None
    
    #i2c接続 20pin,21pinを使用し、100kHzで通信する
    i2c = I2C(0,sda=Pin(20), scl = Pin(21) ,freq=100000)

#BNO055のセンサーデータをリセットさせる
    devices = i2c.scan()
    print("I2C devices:", devices)
    

#以下のコードを実行してからi2c.scan()をするとキャリブレーションが0から進まなかった
    bno = BNO055(i2c)

    @classmethod
    def get_heading(cls):
        cal = False
        while True:
            try:
                if not cal:
                    cls.sys , cls.gyro ,  cls.accel , cls.mag = cls.bno.cal_status()
                    print(cls.sys ,cls.gyro , cls.accel , cls.mag )
            
                    if cls.sys ==3 and cls.gyro == 3 and cls.accel == 3 and cls.mag == 3:
                        cal = True
                        time.sleep(1)
                        
                    #cal = True
                    time.sleep(0.5)
                    continue


                heading , roll , pitch = cls.bno.euler()
                return heading
        
        
        
            except Exception as e:
                print(f"エラー(1秒後に再試行します)")
                time.sleep(1)
            continue
