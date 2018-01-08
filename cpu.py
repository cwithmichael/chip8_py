import random
import logging
from chip8_errors import *

LOG_FILENAME = 'chip8.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)


class Cpu():
    """Acts as the 'cpu' for the Chip-8."""
    fontset = [
        0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
        0x20, 0x60, 0x20, 0x20, 0x70,  # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
        0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
        0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
        0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
        0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
        0xF0, 0x80, 0xF0, 0x80, 0x80   # F
    ]

    MEMORY_SIZE = 0x1000
    KEY_SIZE = 0x10
    STACK_SIZE = 0x10
    REG_SIZE = 0x10
    FONTSET_SIZE = 80
    GFX_SIZE = 0x800

    def __init__(self):
        self.gfx = [False for x in range(64*32)]
        self.opcode = 0
        self.memory = [0 for x in range(Cpu.MEMORY_SIZE)]
        self.key = [False for x in range(Cpu.KEY_SIZE)]
        self.stack = [0 for x in range(Cpu.STACK_SIZE)]
        self.register = [0 for x in range(Cpu.REG_SIZE)]
        self.pc = 0
        self.sp = 0
        self.index = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.draw_flag = False
        self.play_sound = False
        self.decoded_opcode = {"x": 0, "y": 0, "nn": 0, "nnn": 0}
        random.seed()

    def reset(self):
        """Resets the cpu to initial state"""
        self.pc = 0x200
        self.opcode = 0
        self.index = 0
        self.sp = 0
        for i in range(Cpu.GFX_SIZE):
            self.gfx[i] = 0
        for i in range(Cpu.STACK_SIZE):
            self.stack[i] = 0
        for i in range(Cpu.KEY_SIZE):
            self.key[i] = False
        for i in range(Cpu.MEMORY_SIZE):
            self.memory[i] = 0
        for i in range(Cpu.FONTSET_SIZE):
            self.memory[i] = Cpu.fontset[i]

    def cycle(self):
        """Mimicks a cycle for the Chip-8 interpreter"""
        self.fetch_opcode()
        self.decode_opcode()
        self.execute_opcode()
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            if self.sound_timer == 1:
                self.play_sound = True
            self.sound_timer -= 1

    def fetch_opcode(self):
        """Fetches the current opcode from memory"""
        self.opcode = (self.memory[self.pc] & 0xFF) << 8 | (self.memory[self.pc + 1] & 0xFF)

    def decode_opcode(self):
        """Decomposes the current opcode"""
        self.decoded_opcode["x"] = (self.opcode & 0x0F00) >> 8
        self.decoded_opcode["y"] = (self.opcode & 0x00F0) >> 4
        self.decoded_opcode["nn"] = self.opcode & 0x00FF
        self.decoded_opcode["nnn"] = self.opcode & 0x0FFF

    def execute_opcode(self):
        """Executes the current opcode and modifies the program counter"""
        opcode_id = (self.opcode & 0xF000)
        x = self.decoded_opcode["x"]
        y = self.decoded_opcode["y"]
        nn = self.decoded_opcode["nn"]
        nnn = self.decoded_opcode["nnn"]

        if opcode_id == 0:
            op = self.opcode & 0x000f
            #00E0 -> Clears the screen
            if op == 0:
                for i in range(Cpu.GFX_SIZE):
                    self.gfx[i] = False
                self.draw_flag = True
                self.pc += 2
            #00EE -> Returns from a subroutine
            elif op == 0xe:
                self.sp -= 1
                self.pc = self.stack[self.sp] & 0xFFFF
                self.pc += 2
            else:
                logging.debug("BAD OPCODE:" + self.opcode)
                raise OpcodeError(self.opcode, "UNKNOWN OPCODE {}".format(self.opcode))
        #1NNN -> Jumpts to address NNN
        elif opcode_id == 0x1000:
            self.pc = nnn & 0xFFFF
        #2NNN -> Calls subroutine at NNN
        elif opcode_id == 0x2000:
            self.stack[self.sp] = self.pc & 0xFFFF
            self.sp = (self.sp + 1) & 0xFFFF
            self.pc = nnn & 0xFFFF
        #3XNN -> Skips the next instruction if VX equals NN
        elif opcode_id == 0x3000:
            if self.register[x] == nn:
                self.pc += 4
            else:
                self.pc += 2
        #4XNN -> Skips the next instruction if VX doesn't equal NN
        elif opcode_id == 0x4000:
            if self.register[x] != nn:
                self.pc += 4
            else:
                self.pc += 2
        #5XY0 -> Skips the next instruction if VX equals VY
        elif opcode_id == 0x5000:
            if self.register[x] == self.register[y]:
                self.pc += 4
            else:
                self.pc += 2
        #6XNN -> Sets VX to NN
        elif opcode_id == 0x6000:
            self.register[x] = nn
            self.pc += 2
        #7XNN -> Adds NN to VX (Carry flag is not changed)
        elif opcode_id == 0x7000:
            self.register[x] =  (self.register[x] + nn) & 0xFF
            self.pc += 2
        elif opcode_id == 0x8000:
            op = self.opcode & 0x000F
            #8XY0 -> Sets VX to the value of VY
            if op == 0:
                self.register[x] = self.register[y]
                self.pc += 2
            #8XY1 -> Sets VX to VX or VY (Bitwise OR operation)
            elif op == 1:
                self.register[x] |= self.register[y]
                self.pc += 2
            #8XY2 -> Sets VX to VX and VY. (Bitwise AND operation)
            elif op == 2:
                self.register[x] &= self.register[y]
                self.pc += 2
            #8XY3 -> Sets VX to VX xor VY.
            elif op == 3:
                self.register[x] ^= self.register[y]
                self.pc += 2
            #8XY4 -> Adds VY to VX. VF is set to 1 when there's a carry
            elif op == 4:
                if self.register[y] > (0xFF - self.register[x]):
                    self.register[0xF] = 1
                else:
                    self.register[0xF] = 0
                self.register[x] = (self.register[x] + self.register[y]) & 0xFF
                self.pc += 2
            #8XY5 -> VY is subtracted from VX.
            #VF is set to 0 when there's a borrow, and 1 when there isn't.
            elif op == 5:
                if self.register[y] > self.register[x]:
                    self.register[0xF] = 0
                else:
                    self.register[0xF] = 1
                self.register[x] -= self.register[y]
                self.pc += 2
            #8XY6 -> Shifts VY right by one and copies the result to VX.
            #VF is set to the value of the lsb of VY before the shift
            elif op == 6:
                self.register[0xF] = self.register[x] & 0x1
                self.register[x] >>= 1
                self.pc += 2
            #8XY7 -> Sets VX to VY minus VX.
            #VF is set to 0 when there's a borrow, and 1 when there isn't.
            elif op == 7:
                if self.register[x] > self.register[y]:
                    self.register[0xF] = 0
                else:
                    self.register[0xF] = 1
                self.register[x] = (self.register[y] - self.register[x]) & 0xFF
                self.pc += 2
            #8XYE -> Shifts VY left by one and copies the result to VX.
            #VF is set to the value of the msb of VY before the shift.
            elif op == 0xe:
                self.register[0xF] = (self.register[x] >> 7) & 0xFF
                self.register[x] = (self.register[x] << 1) & 0xFF
                self.pc += 2
            else:
                logging.debug("BAD OPCODE:" + self.opcode)
                raise OpcodeError(self.opcode, "UNKNOWN OPCODE {}".format(self.opcode))
        #9XY0 -> Skips the next instruction if VX doesn't equal VY
        elif opcode_id == 0x9000:
            if self.register[x] != self.register[y]:
                self.pc += 4
            else:
                self.pc += 2
        #ANNN -> Sets I to the address NNN
        elif opcode_id == 0xa000:
            self.index = nnn & 0xFFFF
            self.pc += 2
        #BNNN -> Jumps to the address NNN plus V0
        elif opcode_id == 0xb000:
            self.pc = (nnn + self.register[0]) & 0xFFFF
        #CXNN -> Sets VX to the result of random number & NN.
        elif opcode_id == 0xc000:
            self.register[x] = random.randint(0, 0xFF) & nn
            self.pc += 2
        #DXYN -> Draws a sprite at coordinate (VX, VY)
        #It has a width of 8 pixels and a height of N pixels.
        elif opcode_id == 0xd000:
            vx = self.register[x]
            vy = self.register[y]
            height = (self.opcode & 0x000F)
            pixel = 0
            self.register[0xF] = 0
            passed = True

            try:
                for yline in range(height):
                    pixel = self.memory[self.index + yline]
                    for xline in range(8):
                        if pixel & (0x80 >> xline):
                            idx = (vx + xline + ((vy + yline) * 64)) % Cpu.GFX_SIZE
                            if self.gfx[idx]:
                                self.register[0xF] = 1
                            self.gfx[idx] ^= True
            except Exception as e:
                logging.debug("REGISTERS: {}".format(self.register))
                logging.debug("OPCODE: {}".format(self.opcode))
                logging.debug("OPCODE ID: {:02X}".format(opcode_id))
                logging.debug("DECODED OPCODE: {}".format(self.decoded_opcode))
                logging.debug("STACK: {}".format(self.stack))
                logging.debug("PC: {}".format(self.pc))
                logging.debug("SP: {}".format(self.sp))
                passed = False

            if not passed:
                raise GpuError(self.gfx, "Bad Graphics {}".format(self.gfx))
            self.draw_flag = True
            self.pc += 2
        elif opcode_id == 0xe000:
            op = self.opcode & 0x00FF
            #EX9E -> Skips the next instruction if key in VX is pressed.
            if op == 0x009e:
                if self.key[self.register[x]]:
                    self.pc += 4
                else:
                    self.pc += 2
            #EXA1 -> Skips the next instruction if key in VX isn't pressed.
            elif op == 0x00a1:
                if not self.key[self.register[x]]:
                    self.pc += 4
                else:
                    self.pc += 2
            else:
                logging.debug("BAD OPCODE:" + self.opcode)
                raise OpcodeError(self.opcode, "UNKNOWN OPCODE {}".format(self.opcode))
        elif opcode_id == 0xf000:
            op = self.opcode & 0x00FF
            #FX07 -> Sets VX to the value of the delay timer.
            if op == 7:
                self.register[x] = self.delay_timer & 0xFF
                self.pc += 2
            #FX0A -> A key press is awaited, and then stored in VX.
            elif op == 0xa:
                keyPressed = False
                for i in range(Cpu.KEY_SIZE):
                    if self.key[i]:
                        self.register[x] = i
                        keyPressed = True
                if not keyPressed:
                    return
                self.pc += 2
            #FX15 -> Sets the delay timer to VX.
            elif op == 0x0015:
                self.delay_timer = self.register[x]
                self.pc += 2
            #FX18 -> Sets the sound timer to VX.
            elif op == 0x0018:
                self.sound_timer = self.register[x]
                self.pc += 2
            #FX1E -> Adds VX to I
            elif op == 0x001e:
                if (self.index + self.register[x]) > 0xFFF:
                    self.register[0xF] = 1
                else:
                    self.register[0xF] = 0
                self.index = (self.index + self.register[x]) & 0xFFFF
                self.pc += 2
            #FX29 -> Sets I to the location of the sprite for character in VX.
            elif op == 0x0029:
                self.index = (int(self.register[x]) * 0x5) & 0xFFFF
                self.pc += 2
            #FX33 -> Stores the binary-coded decimal representation of VX
            elif op == 0x0033:
                self.memory[self.index] = int(self.register[x] / 100) & 0xFF
                self.memory[self.index + 1] = (int(self.register[x] / 10) % 10) & 0xFF
                self.memory[self.index + 2] = ((self.register[x] % 100) % 10) & 0xFF
                self.pc += 2
            #FX55 -> Stores V0 to VX in memory
            #starting at address I(index)
            elif op == 0x0055:
                for i in range(x+1):
                    self.memory[self.index + i] = self.register[i] & 0xFF
                self.index += x + 1
                self.pc += 2
            #FX65 -> Fills V0 to VX with values from memory
            #starting at address I(index)
            elif op == 0x0065:
                for i in range(x+1):
                    self.register[i] = self.memory[(self.index + i)] & 0xFF
                self.index += x + 1
                self.pc += 2
            else:
                logging.debug("BAD OPCODE:" + self.register)
                raise OpcodeError(self.opcode, "UNKNOWN OPCODE {}".format(self.opcode))
        else:
            logging.debug("BAD OPCODE:" + self.register)
            raise OpcodeError(self.opcode, "UNKNOWN OPCODE {}".format(self.opcode))
