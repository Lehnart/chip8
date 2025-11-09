from dataclasses import dataclass
from font import DEFAULT_FONT
import time
import ctypes
import pygame 
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chip8.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('chip8')

@dataclass
class Instruction:
    op : int 
    operand : int
    x : int 
    y : int 
    n : int 
    nn : int 
    nnn : int 

class Chip8:

    def __init__(self, rom, font = DEFAULT_FONT, ):
        pygame.init()
        self.pixel_size = 10
        self.width = 64
        self.height = 32
        self.screen = pygame.display.set_mode((self.width*self.pixel_size, self.height*self.pixel_size))
        pygame.display.set_caption('CHIP-8 Emulator')

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
        
        for i in range(len(rom)):
            self.memory[i+512] = rom[i]
        self.pc = 512

    def run(self):
        while(True):
            for event in pygame.event.get():
                logger.debug("New event : " + str(event))
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.update_display()
            self.update_timers()
            self.check_inputs()
            self.emulate()
        
    def update_display(self):
        if time.time() - self.last_refresh > 1./60.:
            self.refresh_display()
            self.last_refresh = time.time()

    def refresh_display(self):
        self.screen.fill((0, 0, 0))
        for y in range(self.height):
            for x in range(self.width):
                
                rect = pygame.Rect(x * self.pixel_size + 1, y * self.pixel_size + 1, self.pixel_size - 2, self.pixel_size - 2)
                if self.display[y][x] :  self.screen.fill((255, 255, 255), rect)
                else : self.screen.fill((32, 32, 32), rect)
        pygame.display.flip()

    def update_timers(self):
        if time.time() - self.last_timer_update > 1./60.:
            self.sound_timer -= 1
            self.delay_timer -= 1
            self.sound_timer = 0 if self.sound_timer < 0 else self.sound_timer
            self.delay_timer = 0 if self.delay_timer < 0 else self.delay_timer
            self.last_timer_update = time.time()

    def check_inputs(self):
        keys = pygame.key.get_pressed()
        self.inputs[0][0] = keys[pygame.K_1]
        self.inputs[0][1] = keys[pygame.K_2]
        self.inputs[0][2] = keys[pygame.K_3]
        self.inputs[0][3] = keys[pygame.K_4]
        self.inputs[1][0] = keys[pygame.K_a]
        self.inputs[1][1] = keys[pygame.K_z]
        self.inputs[1][2] = keys[pygame.K_e]
        self.inputs[1][3] = keys[pygame.K_r]
        self.inputs[2][0] = keys[pygame.K_q]
        self.inputs[2][1] = keys[pygame.K_s]
        self.inputs[2][2] = keys[pygame.K_d]
        self.inputs[2][3] = keys[pygame.K_f]
        self.inputs[3][0] = keys[pygame.K_w]
        self.inputs[3][1] = keys[pygame.K_x]
        self.inputs[3][2] = keys[pygame.K_c]
        self.inputs[3][3] = keys[pygame.K_v]

    def emulate(self):
        if time.time() - self.last_execution > 1./10.:
            logger.debug("fetch code")
            op = self.fetch()
            logger.debug("op " + hex(op))
            instruction = self.decode(op)
            logger.debug("instruction " + str(instruction))
            self.execute(instruction)
            self.last_execution = time.time()

    def fetch(self):
        op = bytearray(2)
        op[0] = self.memory[self.pc]
        op[1] = self.memory[self.pc+1]
        op = int.from_bytes(op)
        self.pc += 2
        return op 

    def decode(self, op):
        operand = (op & 0xF000) >> 12
        x = (op & 0x0F00) >> 8
        y = (op & 0x00F0) >> 4
        n = op & 0x000F
        nn = op & 0x00FF
        nnn = op & 0x0FFF
        return Instruction(op, operand, x, y, n, nn, nnn)
    
    def execute(self, instruction):
        if instruction.op == 0x00E0:
            logger.debug("Clear screen")
            self.clear_screen()

        elif instruction.operand == 0x1 :
            logger.debug("Jump to instruction " + str(instruction.nnn))
            self.pc = instruction.nnn

        elif instruction.operand == 0x6 :
            logger.debug("Set register " + str(instruction.x) + " to " + str(instruction.nn))
            self.variable_registers[instruction.x] = instruction.nn

        elif instruction.operand == 0x7 :
            logger.debug("Add to register " + str(instruction.x) + " the value " + str(instruction.nn))
            self.variable_registers[instruction.x] += instruction.nn

        elif instruction.operand == 0xa :
            logger.debug("Set index register to " + str(instruction.nnn))
            self.index_register = instruction.nnn

        elif instruction.operand == 0xD :
            logger.debug("Draw sprite ")
            x = self.variable_registers[instruction.x] % 64
            y = self.variable_registers[instruction.y] % 32
            self.variable_registers[-1] = 0
            self.draw_sprite(instruction, x, y)

        else :
            raise Exception("UNKNOWN INSTRUCTION " + str(hex(instruction.op)) )

    def draw_sprite(self, instruction:Instruction, cx, cy):
        x = cx 
        y = cy 
        logger.debug("x " + str(x) + " y " + str(y))
        for i in range (instruction.n):
            logger.debug("Drawing row " + str(i))
            if y >= 32 : break
            b = self.memory[self.index_register + i]
            for bit in range(8):
                sprite_pixel = (b >> (7 - bit)) & 1
                logger.debug("value at pixel " + str(x) + " " + str(y) + " = " + str(sprite_pixel))
                if x >= 64 : 
                    break
                if self.display[y][x] is True and sprite_pixel == 1 :
                    self.variable_registers[-1] = 1
                    self.display[y][x] = False 
                elif self.display[y][x] is False and sprite_pixel == 1 :
                    self.display[y][x] = True 
                x += 1
            x = cx
            y += 1


    def clear_screen(self):
        for i in range(len(self.display)):
            for j in range(len(self.display[i])):
                self.display[i][j] = False
