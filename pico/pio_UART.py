import machine
import rp2
import time

# --- 設定の一元管理用 ---
class UARTParams:
    TX_PIN = 2
    RX_PIN = 3
    BAUDRATE = 9600
    SM_TX_ID = 0
    SM_RX_ID = 1

class PIOUART:
    # クラス変数：どこからでもアクセス可能な共有リソース
    _rx_buf = bytearray()
    sm_tx = None
    sm_rx = None
    _initialized = False

    @classmethod
    def init(cls):
        """明示的に呼び出す初期化メソッド"""
        if cls._initialized:
            return

        pio_freq = UARTParams.BAUDRATE * 8
        
        # TX 初期化
        cls.sm_tx = rp2.StateMachine(
            UARTParams.SM_TX_ID, _pio_uart_tx, freq=pio_freq,
            sideset_base=machine.Pin(UARTParams.TX_PIN),
            out_base=machine.Pin(UARTParams.TX_PIN),
        )
        cls.sm_tx.active(1)

        # RX 初期化
        pin_rx = machine.Pin(UARTParams.RX_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
        cls.sm_rx = rp2.StateMachine(
            UARTParams.SM_RX_ID, _pio_uart_rx, freq=pio_freq,
            in_base=pin_rx,
        )
        
        cls.sm_rx.irq(cls._rx_handler)
        cls.sm_rx.active(1)
        cls._initialized = True

    @classmethod
    def _rx_handler(cls, sm):
        while sm.rx_fifo() > 0:
            # クラス変数 _rx_buf に蓄積
            cls._rx_buf.append((sm.get() >> 24) & 0xFF)

    @classmethod
    def write(cls, data):
        if isinstance(data, str):
            data = data + "\n"
            data = data.encode('utf-8')
        for byte in data:
            cls.sm_tx.put(byte)

    @classmethod
    def any(cls):
        return len(cls._rx_buf)

    @classmethod
    def read(cls):
        data = cls._rx_buf[:]
        cls._rx_buf[:] = b''
        return data
    
    @classmethod
    def readline(cls):
        # バッファ内に改行コードがあるか確認
        if b'\n' in cls._rx_buf:
            # 改行コードの位置を探す
            idx = cls._rx_buf.find(b'\n') + 1
            # 改行までのデータを切り出す
            line = cls._rx_buf[:idx]
            # バッファから切り出した分を削除する
            cls._rx_buf[:] = cls._rx_buf[idx:]
            return line.decode("utf-8").rstrip()
        return None

# --- PIOのアセンブリ定義はクラス外のグローバルでOK ---
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_HIGH, out_init=rp2.PIO.OUT_HIGH, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def _pio_uart_tx():
    pull().side(1) [7]
    set(x, 7).side(0) [7]
    label("bitloop")
    out(pins, 1)
    jmp(x_dec, "bitloop") [6]
    nop().side(1) [6]

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_RIGHT, autopush=True, push_thresh=8)
def _pio_uart_rx():
    wait(0, pin, 0)
    set(x, 7) [9]
    label("bitloop")
    in_(pins, 1)
    jmp(x_dec, "bitloop") [6]
    irq(rel(0))
    
    
    
if __name__ == "__main__":
    PIOUART.init()
    while True:
        line = PIOUART.readline()
        if line is not None:
            print(f"{line}")
            

        # 3. 送信（文字列やバイト列を送る）
        PIOUART.write("Hello from Pico!")
    
        time.sleep(1)

