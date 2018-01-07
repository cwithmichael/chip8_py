class Chip8Error(Exception):
    pass

class OpcodeError(Chip8Error):
    def __init__(self, opcode, message):
        self.opcode = opcode
        self.message = message

class GpuError(Chip8Error):
    def __init__(self, current_gfx, message):
        self.current_gfx = current_gfx
        self.message = message