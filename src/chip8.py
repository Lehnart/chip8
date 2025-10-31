from font import DEFAULT_FONT
import time
import ctypes

class Chip8:

    def __init__(self, font = DEFAULT_FONT):
        self.memory = bytearray(4 * 1024)
        self.pc = 0 
        self.last_execution = time.time()

        self.index_register = 0
        self.variable_registers = [0]*16
        self.stack = []

        self.sound_timer = 0
        self.delay_timer = 0
        self.last_timer_update = time.time()
        
        self.display = [[False] * 64 for _ in range(32)]
        self.last_refresh = time.time()

        self.inputs = [ [False]*4 for i in range(4)]
        for i in range(len(font)):
            self.memory[i] = font[i]

    def run(self):
        while(True):
            self.update_display()
            self.update_timers()
            self.check_inputs()
            self.emulate()
        
    def update_display(self):
        if time.time() - self.last_refresh > 1./60.:
            self.refresh_display()
            self.last_refresh = time.time()

    def refresh_display(self):
        pass 

    def update_timers(self):
        if time.time() - self.last_timer_update > 1./60.:
            self.sound_timer -= 1
            self.delay_timer -= 1
            self.sound_timer = 0 if self.sound_timer < 0 else self.sound_timer
            self.delay_timer = 0 if self.delay_timer < 0 else self.delay_timer
            self.last_timer_update = time.time()

    def check_inputs(self):

        print(self.inputs)
        try:    
            self.inputs[0][0] = (ctypes.windll.user32.GetAsyncKeyState(0x31) & 0x8000) != 0
            self.inputs[0][1] = (ctypes.windll.user32.GetAsyncKeyState(0x32) & 0x8000) != 0
            self.inputs[0][2] = (ctypes.windll.user32.GetAsyncKeyState(0x33) & 0x8000) != 0
            self.inputs[0][3] = (ctypes.windll.user32.GetAsyncKeyState(0x34) & 0x8000) != 0
            self.inputs[1][0] = (ctypes.windll.user32.GetAsyncKeyState(0x41) & 0x8000) != 0
            self.inputs[1][1] = (ctypes.windll.user32.GetAsyncKeyState(0x5A) & 0x8000) != 0
            self.inputs[1][2] = (ctypes.windll.user32.GetAsyncKeyState(0x45) & 0x8000) != 0
            self.inputs[1][3] = (ctypes.windll.user32.GetAsyncKeyState(0x52) & 0x8000) != 0
            self.inputs[2][0] = (ctypes.windll.user32.GetAsyncKeyState(0x51) & 0x8000) != 0
            self.inputs[2][1] = (ctypes.windll.user32.GetAsyncKeyState(0x53) & 0x8000) != 0
            self.inputs[2][2] = (ctypes.windll.user32.GetAsyncKeyState(0x44) & 0x8000) != 0
            self.inputs[2][3] = (ctypes.windll.user32.GetAsyncKeyState(0x46) & 0x8000) != 0
            self.inputs[3][0] = (ctypes.windll.user32.GetAsyncKeyState(0x57) & 0x8000) != 0
            self.inputs[3][1] = (ctypes.windll.user32.GetAsyncKeyState(0x58) & 0x8000) != 0
            self.inputs[3][2] = (ctypes.windll.user32.GetAsyncKeyState(0x43) & 0x8000) != 0
            self.inputs[3][3] = (ctypes.windll.user32.GetAsyncKeyState(0x56) & 0x8000) != 0

        except Exception:
            pass

    def emulate(self):
        if time.time() - self.last_execution > 1./700.:
            op = self.fetch()
            self.decode(op)
            self.execute()
            self.last_execution = time.time()

    def fetch(self):
        op = bytearray(2)
        op[0] = self.memory[self.pc]
        op[1] = self.memory[self.pc+1]
        self.pc += 2
        return op 

    def decode(self, op):
        operand = op & 0xF000
        x = op & 0x0F00
        y = op & 0x00F0
        n = op & 0x000F
        nn = op & 0x00FF
        nnn = op & 0x0FFF
        