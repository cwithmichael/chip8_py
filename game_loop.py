import pygame

from cpu import Cpu

def load_game(filename):
    """Loads a Chip-8 game by reading in a file in binary mode"""
    bytes = []
    with open(filename, "rb") as f:
        b = f.read(1)
        bytes.append(int.from_bytes(b, byteorder='big'))
        while b != b"":
            b = f.read(1)
            bytes.append(int.from_bytes(b, byteorder='big'))

    return bytes


def game_loop():
    pygame.init()
    beep = pygame.mixer.Sound("bell.ogg")
    size = width, height = 640, 320
    clock = pygame.time.Clock()
    black = 0, 0, 0
    white = 255, 255, 255
    fps = 60
    gfx_width = 64
    gfx_height = 32
    scale_factor = 10

    screen = pygame.display.set_mode(size)
    game = load_game("PONG2")
    cpu = Cpu()
    cpu.reset()
    i = 0
    for x in range(len(game)):
        cpu.memory[i + 0x200] = game[i]
        i += 1
    run = True
    while (run):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            run = False
        #Row 1 of keys
        cpu.key[1] = keys[pygame.K_1]
        cpu.key[2] = keys[pygame.K_2]
        cpu.key[3] = keys[pygame.K_3]
        cpu.key[0xc] = keys[pygame.K_4]
        #Row 2 of keys
        cpu.key[4] = keys[pygame.K_q]
        cpu.key[5] = keys[pygame.K_w]
        cpu.key[6] =  keys[pygame.K_e]
        cpu.key[0xd] = keys[pygame.K_r]
        #Row 3 of keys
        cpu.key[7] = keys[pygame.K_a]
        cpu.key[8] = keys[pygame.K_s]
        cpu.key[9] = keys[pygame.K_d]
        cpu.key[0xe] = keys[pygame.K_f]
        #Row 4 of keys
        cpu.key[0xa] = keys[pygame.K_z]
        cpu.key[0x0] = keys[pygame.K_x]
        cpu.key[0xb] = keys[pygame.K_c]
        cpu.key[0xf] = keys[pygame.K_v]

        cpu.cycle()
        if cpu.play_sound:
            pygame.mixer.Sound.play(beep)
            cpu.play_sound = False
        if cpu.draw_flag:
            clock.tick(fps)
            for i in range(gfx_height):
                for j in range(gfx_width):
                    if cpu.gfx[i * gfx_width + j]:
                        screen.fill(white, (j * scale_factor, i * scale_factor, scale_factor, scale_factor))
                    else:
                        screen.fill(black, (j * scale_factor, i * scale_factor, scale_factor, scale_factor))
            pygame.display.flip()
            cpu.draw_flag = False


    pygame.quit()

if __name__ == '__main__':
    game_loop()
