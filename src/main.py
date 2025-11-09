from chip8 import Chip8
import sys 

def main():
    rom = None
    if len(sys.argv) >= 2:
        print(sys.argv[1])
        with open(sys.argv[1], 'rb') as f : 
            rom = f.read()

    Chip8(rom).run()

if __name__ == "__main__":
    main()