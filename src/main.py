#  This is a 'work-in-progress'.
#  The current script is an existing 'snake game' that I ported to
#  an Unexpected Maker TinyPICO Explorer Shield,
#  Initially during the port, images and texts were (vertically) only for about sixty percent.
#  I discovered that, in ST7789.py, in function __init__(), changing:
#  'self._offset = bytearray([0,0])'  into 'self._offset = bytearray([0,80])' solved the problem.
#  I modified the snake game in various ways. I moved the snake class to a separate file:
#  snake.py. I added various functions to accomodate the hardware as the game.
#  This script contains 21 functions (as of 2022-08-23).
#
#  License: MIT (see attached LICENSE file)
#
from micropython import const
import esp32
from machine import SoftI2C, Pin, Timer, PWM, SPI, ADC
import time, random, framebuf, bitmaps, math, notes
from ST7789 import TFT, TFTColor
import mpr121
import sysfont as sysfont
import tinypico_helper as TinyPICO
from snake import Snake

use_bmp = True

if not use_bmp:
    import bitmaps  # as bitmaps

# Constants not defined in tinypico_helper.py

# Display
DISP_RES = const(9)
DISP_CS = const(5)
DISP_DC = const(15)
BUZZER = const(25)

SD_DETECT = const(26)
SD_CS = const(5)
IMU_INT = const(33)
LCD_BL = const(27)
AMB_LIGHT = const(32)  # Digital only

# Globals
my_debug = False
use_sound = True

RED = TFTColor(0xFF, 0x00, 0x00)

font = sysfont.sysfont
if my_debug:
    print("type(font)= ", type(font))

snake = None
btn = 0
game_state = -1 #0 = menu, 1 = playing, 2 = pause, 3 = gameover
game_state_changed = False
fruit_interval = 10
fruit_next = 0
default_freq = 1
left = -1
right = 1
hori = 0
vert = 1
hori2 = 2
vert2 = 3
yofs = []
dflt_bg = None

rotation = 2 
spi = SPI(2, baudrate=40000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
tft = TFT(spi, 4, 14, 9) # DC Pin(4),  CS Pin(14), Reset Pin(9),
tft.initr()
tft.set_offset(0, 80) 
tft.rgb()  # defaults to True (that's what I intend here)
tft.invertcolor(True)
dflt_bg = TFT.WHITE
tft.rotation(rotation)
color_order = tft.rgb(False)  # BGR  This gives character letters in BLUE
tft.fill(TFT.BLACK)

scrn_size = tft.size()
if my_debug:
    print("app startup: display dimensions: ", scrn_size)
disp_height = scrn_size[vert] # set the global vars accordingly
disp_width = scrn_size[hori]  # idem
yofs = {0: 20, 1: disp_height//2, 2: disp_height-20}

# idea from deshipu (Discord: Radomir Dopieralski#9427)
# to get rid of a 40% black area on the lower half of the display,
# but didn't work for this hardware setup. 
# tft._setwindowloc((0,68),(disp_width - 1,disp_height - 1 + 68))
# Instead alteration of the h-value of self.offset in __init__() of ST7789.py did the job

# Begin

# Turn off the power to the DotStar
TinyPICO.set_dotstar_power( False )

# Configure I2C for controlling anything on the I2C bus
# Software I2C only for this example but the next version of MicroPython for the ESP32 supports hardware I2C too
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

mpr = mpr121.MPR121(i2c) # Touch object

game_state = -1 #0 = menu, 1 = playing, 2 = pause, 3 = gameover
game_state_changed = False
fruit_interval = 10
fruit_next = 0

def setup():
    global dflt_bg
    
    if dflt_bg == 0:
        t = "BLACK"
    elif dflt_bg == 65535:
        t = "WHITE"
    elif dflt_bg == 32768:
        t = "MAROON"
    else:
        t = "OTHER COLOR"
    s = "default background color is set to: " + t + " = 0x{:x}".format(dflt_bg)
    #print(s)

    #time.sleep(5)

    if my_debug:
        print("Size received from TFT: width = {}, height = {}".format(tft.size()[vert], tft.size()[hori]))
        
def rd_logo():
    f = None
    fn = 'um_logo_240x240.bmp' # tinyPICO_logo_240x240.bmp'
    try:
        f=open(fn, 'rb')
    except OSError as exc:
        if exc.args[0] == 2:
            print("file \"{}\" not found".format(fn))
            return

    if f.read(2) == b'BM':  #header
        dummy = f.read(8) #file size(4), creator bytes(4)
        offset = int.from_bytes(f.read(4), 'little') # offset = 54
        hdrsize = int.from_bytes(f.read(4), 'little') # hdrsize = 40
        width = int.from_bytes(f.read(4), 'little')
        height = int.from_bytes(f.read(4), 'little')
        if my_debug:
            print("offset=", offset)
            print("hdrsize=", hdrsize)
            print("width=", width)
            print("height=", height)
        if int.from_bytes(f.read(2), 'little') == 1: #planes must be 1
            depth = int.from_bytes(f.read(2), 'little')
            compress_method = int.from_bytes(f.read(4), 'little')
            if my_debug:
                print("depth=", depth)
                print("compress_method=", compress_method)
            if depth == 24 and compress_method == 0: #compress method == uncompressed
                rowsize = (width * 3 + 3) & ~3
                if my_debug:
                    print("Image size:", width, "x", height)
                    print("rowsize=", rowsize)
                if height < 0:
                    height = -height
                    if my_debug:
                        print("height reset to ", height)
                    flip = False
                else:
                    flip = True
                w, h = width, height
                if my_debug:
                    print("w=", w)
                    print("lcd_w=", disp_width)
                    print("h=", h)
                    print("lcd_h=", disp_height)
                #"""
                if w > disp_width: w = disp_width
                if h > disp_height: h = disp_height
                tft._setwindowloc((0,0),(w - 1,h - 1))
                colorData = bytearray(2*height) # was: 2*240
                if my_debug:
                    print("flip=", flip)
                for row in range(h):
                    if flip:
                        pos = offset + (height - 1 - row) * rowsize
                    else:
                        pos = offset + row * rowsize
                    if f.tell() != pos:
                        dummy = f.seek(pos)
                    colorDataIndex = 0
                    readBgrNum = 6
                    for col in range(0,w,6):
                        bgr = f.read(18)
                        bgrIndex = 0
                        for t in range(6):
                            color = ((bgr[bgrIndex+2] & 0xF8) << 8) | ((bgr[bgrIndex+1] & 0xFC) << 3) | (bgr[bgrIndex+0] >> 3)
                            colorData[colorDataIndex] = color >> 8
                            colorData[colorDataIndex+1] = color
                            colorDataIndex = colorDataIndex + 2
                            bgrIndex = bgrIndex + 3
                    tft._writedata(colorData)

# Sound
def play_boot_music():
    speaker = PWM(Pin(25), freq=20000, duty=512)
    boot_sound = [notes.D4, 0, notes.G4, 0, notes.D4, 0, notes.A4, 0]
    for i in boot_sound:
        if i == 0:
            speaker.freq(1)
            time.sleep_ms(50)
            pass
        else:
            speaker.freq(i)
            time.sleep_ms(250)

    speaker.freq(1)
    speaker.deinit()
    
def play_death():
    speaker = PWM(Pin(25), freq=20000, duty=512)
    speaker.freq(notes.D4)
    time.sleep_ms(200)
    speaker.freq(1)
    time.sleep_ms(25)
    speaker.freq(notes.A2)
    time.sleep_ms(400)
    speaker.freq(1)
    speaker.deinit()

def play_sound( note, duration ):
    speaker = PWM(Pin(25), freq=20000, duty=512)
    speaker.freq(note)
    time.sleep_ms(duration)
    speaker.freq(1)
    speaker.deinit()
    
def play_ate_fruit_sound():
    speaker = PWM(Pin(25), freq=20000, duty=512)
    ate_sound = [notes.C7, notes.E7, notes.C7, notes.E7]
    le = len(ate_sound)
    for i in range(le):
        speaker.freq(ate_sound[i])
        time.sleep_ms(200)
        speaker.freq(1)
        if i < le-1:
            time.sleep_ms(25)
    speaker.deinit()
    
def player_turn(dir):
    global snake
    snake.set_dir(dir)

def switch_state( new_state ):
    global game_state, game_state_changed
    if game_state == new_state:
        pass
    else:
       game_state = new_state
       game_state_changed = True


# Helpers

def text_horiz_centred(fb, text, y, char_width=3):
    #fb.text(text, (fb.width - len(text) * char_width) // 2, y)
    w_offset = 90
    aPos = ((disp_width - len(text) * char_width) // 2 - w_offset, y) # // 2 -90, y+50)
    if my_debug:
        print("text= {}, aPos= {}".format(text, aPos))
    #   def text( self, aPos, aString, aColor, aFont, aSize = 1, nowrap = False ) :
    fb.text(aPos, text, RED, font, char_width)
    time.sleep(2)

"""
In Pimoroni PicoSystem on GitHub /libraries/picosystem.hpp
  // input pins
  enum button {
    UP    = 23,
    DOWN  = 20,
    LEFT  = 22,
    RIGHT = 21,
    A     = 18,
    B     = 19,
    X     = 17,
    Y     = 16
  };
  
  My equivalent:
  butDict = {"UP": 128,
           "DOWN": 8,
           "LEFT": 16,
           "RIGHT": 32,
           "A": 512,
           "B": 256,
           "X": 2048,
           "Y": 1024}

Results from Arduino sketch:
'TinyPICO_Explorer_Shield_Tester.ino':
+-------------+-----------------+
| IDE output: |  Button Touched |
+-------------+-----------------+
|  0 released | button marked 3 |
|  1 released | button marked 2 |
|  2 released | button marked 1 |
|  3 released | triangle DOWN   |
|  4 released | triangle LEFT   |
|  5 released | triangle RIGHT  |
|  6 released | button marked 4 |
|  7 released | triangle UP     |
|  8 released | button marked B |
|  9 released | button marked A |
| 10 released | button marked Y |
| 11 released | button marked X |
+-------------+-----------------+

# mpr = mpr121.MPR121(i2c) # Touch object
# mpr.touched() values:
# 3 = 1
# 2 = 2
# 1 = 4
# Triangle DN = 8
# Triangle LT = 16
# Triangle RT = 32
# Triangle 4 (Center) = 64
# Triangle UP = 128
# B = 256
# A = 512
# Y = 1024
# X = 2048
"""
touchDict0 = {
            1: "3",
            2: "2",
            3: "1",
            4: "DN",
            5: "LT",
            6: "RT",
            7: "4",
            8: "UP",
            9: "B",
            10: "A",
            11: "Y",
            12: "X"}

touchDict1 = {
            1: "3",
            2: "2",
            4: "1",
            8: "DN",
            16: "LT",
            32: "RT",
            64: "4",
            128: "UP",
            256: "B",
            512: "A",
            1024: "Y",
            2048: "X"}

touchDict2 = {
            1: 1,
            2: 2,
            4: 3,
            8: 4,
            16: 5,
            32: 6,
            64: 7,
            128: 8,
            256: 9,
            512: 10,
            1024: 11,
            2048: 12}

touchDict3 = {
            1: 1,
            2: 2,
            3: 4,
            4: 8,
            5: 16,
            6: 32,
            7: 64,
            8: 128,
            9: 256,
            10: 512,
            11: 1024,
            12: 2048}

#    b11                                                      b0
# | 2048 | 1024 | 512 | 256 | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |

# buttonStatesDict[0] is a dummy item, so we can count from BUT_1 ... BUT_12
buttonStatesDict = { 0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0 }

# Buttons

BUT_1_VAL  = const(1)     # 3
BUT_2_VAL  = const(2)     # 2
BUT_3_VAL  = const(4)     # 1
 
BUT_4_VAL  = const(8)     # DN 
BUT_5_VAL  = const(16)    # LT
BUT_6_VAL  = const(32)    # RT
BUT_7_VAL  = const(64)    # 4 (Center)
BUT_8_VAL  = const(128)   # UP

BUT_9_VAL  = const(512)   # A
BUT_10_VAL = const(256)   # B
BUT_11_VAL = const(1024)  # Y
BUT_12_VAL = const(2048)  # X

BUT_1  = const(1)   # 3
BUT_2  = const(2)   # 2
BUT_3  = const(3)   # 1
 
BUT_4  = const(4)   # DN 
BUT_5  = const(5)   # LT
BUT_6  = const(6)   # RT
BUT_7  = const(7)   # 4 (Center)
BUT_8  = const(8)   # UP

BUT_9  = const(9)   # A
BUT_10 = const(10)  # B
BUT_11 = const(11)  # Y
BUT_12 = const(12)  # X

last_button_press_time = 0
last_button_nr = 0

"""
    ck_btns()
    Params: None
    Return: string. Name of button touched
            If no button touched: return "None"
"""
def ck_btns():
    btn = 0
    k = mpr.touched()
    
    if k in touchDict2.keys(): 
        btn = touchDict2[k] # return value 1...12
        buttonStatesDict[btn] = 1 # Set button stated
    return btn

def clr_btnStates():
    le = len(buttonStatesDict)
    for i in range(le):
        buttonStatesDict[i] = 0

def process_button_1():  # LT button pressed
    if game_state == 1:
        if 5 in buttonStatesDict.keys():
            buttonStatesDict[5] = 1
        if my_debug:
            print("Pressed Button LT")
        player_turn(3)
        if use_sound:
            play_sound(notes.C6, 200)

def process_button_2():  # RT button pressed
    if 10 in buttonStatesDict.keys():
        buttonStatesDict[10] = 1
    """
    if game_state == 0:
        switch_state(1)
    elif game_state == 3:
        switch_state(0)
    """
    if my_debug:
        print("Pressed Button RT")
    player_turn(1)
    if use_sound:
        play_sound(notes.D6, 200)

def process_button_3():  # A button pressed
    if game_state == 1:
        if 9 in buttonStatesDict.keys():
            buttonStatesDict[9] = 1
        if my_debug:
            print("Pressed Button UP")
        player_turn(0)
        if use_sound:
            play_sound(notes.E6, 200)

def process_button_4():  # B button pressed
    if game_state == 1:
        if 6 in buttonStatesDict.keys():
            buttonStatesDict[6] = 1
        if my_debug:
            print("Pressed Button DN")
        player_turn(2)
        if use_sound:
            play_sound(notes.F6, 200)

def process_button_5():  # Y button pressed
    if 11 in buttonStatesDict.keys():
        buttonStatesDict[11] = 1
    if my_debug:
        print("Pressed Button Y")
    
#                    Button LT     RT     UP      DN
button_handlers = { str(BUT_5): process_button_1,
                    str(BUT_6): process_button_2,
                    str(BUT_8): process_button_3,
                    str(BUT_4): process_button_4 }

def button_press_callback(btn):
    global last_button_press_time
    # block button press as software debounce
    if last_button_press_time < time.ticks_ms():
        
        # add 150ms delay between button presses... might be too much, we'll see!
        last_button_press_time = time.ticks_ms() + 150

        # If the pin is in the callback handler dictionary, call the appropriate function 
        if str(btn) in button_handlers:
            if my_debug:
                print("going to call: {}()".format(button_handlers[str(btn)]))
            button_handlers[str(btn)]()
        else:
            if my_debug:
                print("btn \"{}\" not in button_handlers \"{}\"".format(btn, button_handlers))

    #     # print a debug message if button presses were too quick or a dounce happened
    #     print("Button Bounce - {}ms".format( ( last_button_press_time - time.ticks_ms() ) ) )

# check keys one by one
def handler():
    global game_state, game_state_changed
    TAG = "handler(): "
    btn = ck_btns()
    if btn == 0:
        if my_debug:
            print(TAG+"no button is pressed")
    elif btn == 2 and game_state == 0:
        game_state = 1  # Start the game
        game_state_changed = True
    else:
        if my_debug:
            print(TAG+'Button nr {} touched'.format(touchDict0[btn]))
        #if str(touchDict3[btn]) in button_handlers:  # this check is done in button_press_callback()
        button_press_callback(btn)


# create timer for flashing UI
flasher = Timer(0)
flash_state = False
def flasher_update(timer):
    global flash_state
    flash_state = not flash_state

flasher.init(period=500, mode=Timer.PERIODIC, callback=flasher_update)

"""
def flash_text(x,y,text):
    global flash_state
    if flash_state:
        tft.text((x, y), text, tft.WHITE, font, 2)
    else:
        tft.fillrect( (1, y), (126, 12), 0)
"""

def flash_text(text):
    global flash_state, dflt_bg, disp_width, disp_height
    TAG = "flash_text(): "
    t_bg = dflt_bg
    r = tft.get_rotation()
    le = len(text)
    if le < 8:
        offset = 70 # (disp_width//2) - (le // 2) -
    else:
        offset = 26
    curr_y = get_y()
    if my_debug:
        print(TAG+"disp_width=", disp_width)
        print("x offset= ", offset)
        print("len(text)=", le)
        print("curr_y=", curr_y)
    
    if dflt_bg == TFT.BLACK:
        txt_color = TFT.WHITE
    elif dflt_bg == TFT.WHITE:
        txt_color = TFT.BLACK
    
    if r == 0 or r == 2:
        x = 4 # 24
        y = 210 #curr_y # 84
        x2 = disp_width - 4 # 12
        y2 = y + 12  #126
    elif r == 1 or r == 3:
        x = 84
        y = curr_y # 24
        x2 = disp_width - 4 #126
        y2 = curr_y + 15 # 12

    font_size = 3
    t_bg = TFT.WHITE
    tft.fillrect((1, y), (x2, y2), t_bg)
    for i in range(15):
        if flash_state:
            txt_color = TFT.RED
        else:
            txt_color = t_bg
        tft.text((offset, y+5), text, txt_color, font, font_size)
        time.sleep(0.2)
        flasher_update(flasher)
    time.sleep(0.5)
    tft.fillrect((1, y), (x2, y2), TFT.BLACK)
        
def show_menu():
    # clear the display
    tft.fill(TFT.BLACK)
    # Show welcome message
    text_horiz_centred( tft, " TINY SNAKE", 10 )
    text_horiz_centred( tft, "<  LT | RT >", 40 )
    text_horiz_centred( tft, "/\ UP | DN \/", 70 )
    v = 100
    tft.line((5, v), (234, v), RED) # ,1 )
    text_horiz_centred( tft, "2 Start", 110 )
    text_horiz_centred( tft, "Y End  ", 140 )
    
    time.sleep(3)

# show the menu on start
switch_state(0)
# end of TinyPICO defines

def draw_snake():
    global tft, snake, fruit_next, fruit_interval, my_debug, dflt_bg, last_button_nr, rotation
    # Move the snake and return if we need to clear the tail or if the snake grew
    #check_and_restore_disp_size()
    snake_dims = (6,6)
    fruit_dims = (8,8)
    move = snake.move()
    if snake.is_ate_fruit():
        print("Your score=",snake._score)
        if use_sound:
            play_ate_fruit_sound()
    if my_debug:
        print("draw_snake(): result of snake.move() = [h {:2d}, v {:2d}, h1 {:2d}, v1 {:2d}]".format(move[hori],move[vert], move[hori2], move[vert2]))
        print("last button pressed: ", last_button_nr)

    # The snake tail position is stored in result index 0,1 if it needs to be removed
    # If x or y are > 0 then we remove that pos from the screen

    if move[hori] > 0 or move[vert] > 0:
        tft.fillrect((move[hori], move[vert]), snake_dims, dflt_bg)

    # The last eaten fruit position is stored in indexes 2, 3 if it needs to be removed
    # If x or y are > 0 then we remove that pos from the screen
    if move[hori2] > 0 or move[vert2] > 0:
        tft.fillrect((move[hori2]-1, move[vert2]-1), fruit_dims, dflt_bg)
        if use_sound:
            play_sound(notes.C4,100)

    # Go through the snake positions and draw them
    for pos in snake.get_positions():
        tft.fillrect((pos[hori], pos[vert]), snake_dims, tft.RED)

    # Redraw all fruit
    for pos in snake.get_fruit_positions():
        tft.fillrect((pos[hori]-1, pos[vert]-1), fruit_dims, tft.MAROON)

    # Update the display

    time.sleep( snake.get_speed() )

    # If the snake died in that move, end the game
    if snake.is_dead():
        if use_sound:
            play_death()
        switch_state( 3 )

def setup_new_game():
    global tft, disp_width, disp_height, dflt_bg
    reset_disp(0)
    #check_and_restore_disp_size() # check and restore display dimensions
    #tft.fill(dflt_bg)
    size = tft.size()
    if size[hori] == 80: # not 240?
        # restore dimensions to: 160 x 80
        tft.set_size(160,80) # Not 240 x 240 ?
        print("restored display dimentsions to: ", tft.size())
    if my_debug:
        print("setup_new_game(): current display size is: ", size)
    tft.fillrect((0,0), (tft.size()[vert]-1, tft.size()[hori]-1), dflt_bg)

    #reset variables
    clr_btnStates()
    global snake, fruit_next, fruit_interval, disp_width, disp_height
    #snake.reset( x=62, y=30, len=3, dir=0 )
    #snake.reset(x=disp_width//2, y=yofs[2], len=3, dir=0)
    snake.reset(x=100, y=100, len=3, dir=0)
    fruit_next = time.time() + fruit_interval
    draw_snake()

def get_y():
    if rotation == 0 or rotation == 2:
        return 40 # 65 # (26 + (104-26-2)  was: disp_height//2
    elif rotation == 1 or rotation == 3:
        return 80 # 65 # (26 + (104-26-2)  was: disp_height//2

def clr_fbuf():
    global fbuf
    # was ...,framebuf.MONO_HLSB)
    fbuf = framebuf.FrameBuffer(bytearray(range(disp_width * disp_height * 2)), disp_width, disp_height, framebuf.RGB565)

def set_disp_dimensions():
    global disp_width, disp_height, hori, vert
    r = tft.get_rotation()
    if r == 0 or r == 2:
        disp_height = tft.size()[vert]
        disp_width = tft.size()[hori]
    elif r == 1 or r == 3:
        disp_height = tft.size()[hori]
        disp_width = tft.size()[vert] 

def show_gameover():
    global snake, tft, dflt_bg
    t1 = "YOU SCORED "
    t2 =  "2 - Continue"
    tft.fill(TFT.BLACK) # was: (dflt_bg)
    y = get_y()
    text_horiz_centred( tft, t1 + str( snake.get_score() ), y-20) # yofs[0] )
    text_horiz_centred( tft, t2, y+20) #yofs[2] )

def reset_disp(r_mode):
    global tft, disp_width, disp_height, rotation, snake
    snake_dims = (6,6)
    fruit_dims = (8,8)
    
    if r_mode is None:
        r_mode = 1  # don't reset tft

    if r_mode == 0:
        tft.initr()
        #tft.rotation(0)  # rotation = 270 degs

    #tft.fillrect((0,0), (disp_width-1, disp_height-1), tft.WHITE)
    tft.rotation(rotation)     
    rotation = tft.get_rotation()
    tft._setwindowloc((0,0), (disp_width, disp_height)) # Set a rectangular area for drawing a color to
    set_disp_dimensions()
    snake = Snake( dw=disp_width, dh=disp_height, x=disp_width//2, y=disp_height//2, len=6, dir=0 )  # was: x= 62, y=30, len=6, dir = 0
    snake.set_snake_dims(snake_dims) #(snake_dims[0], snake_dims[1]))
    snake.set_fruit_dims(fruit_dims) # (fruit_dims[0], fruit_dims[1]))
    #snake.set_scrn_size((0, 0, disp_width, disp_height)) # set the limits for the snake playfield
    tft.fill(TFT.BLACK) # tft.WHITE)
    if my_debug:
        print("reset_disp(): rotation changed to: ", rotation)    
        print("yofs =", yofs)

    #tft.fill(aColor = tft.WHITE)
    #tft.fillrect((0,0), (disp_height-1, disp_width-1), tft.WHITE)
    
def check_and_restore_disp_size():
    print("check_and_restore_disp_size(): current display size according to ST7789 class: ", tft.size())
    size_width = tft.size()[hori]
    size_height = tft.size()[vert]
    if size_width == disp_height:
        print("ST7789 display width: {}, previous display height {}".format(size_width, disp_height))
        if size_height == disp_width:  # the h and v are reverse by ??? so correct it
            print("ST7789 display height: {}, previous display width {}".format(size_height, disp_width))
            tft.set_size(disp_height, disp_width)
            print("new set disp w/h: ", tft.size())

tft.fill(TFT.BLACK)

def main():
    global game_state_changed, disp_width, disp_height, last_button_nr, fbuf
    flasher.init(period=500, mode=Timer.PERIODIC, callback=flasher_update)
    t1 = "EXPLORER    "
    t2 = "SHIELD      "
    t3 = "ESP32 INSIDE"
    setup()
    tft.invertcolor(0)
    """
       As long as I am not capable to display the bitmap icon_tinyPICO,
       we will load a TinyPICO logo from a .bmp file.
    """
    if use_bmp:
        rd_logo()
    else:
        print("going to display icon_tinyPICO")
        # Add the TP logo to a frameBuf buffer and show it for 2 seconds
        data = bytearray(bitmaps.icon_tinypico)
        #le = len(data)
        #print("len(bitmaps.icon_tinypico)=", le)
        """
           GS2_HMSB, GS4_HMSB, GS8,
           MONO_HLSB, MONO_HMSB,
           MONO_VLSB,
           MVLSB,
           RGB565
        """
        fbuf = framebuf.FrameBuffer(data, 240*8*2, 240, framebuf.RGB565) # was: framebuf.MONO_HLSB) 
        fbuf.blit(fbuf, 0, 0)
        tft.image( 0,0, disp_width, disp_height, fbuf )
    time.sleep(5)
    tft.invertcolor(1)
    tft.fill(TFT.BLACK)
    tft._setwindowloc((0,0), (disp_width, disp_height)) # restore the window
    clr_fbuf()
    tft.fill(TFT.BLACK)
    
    y = get_y()
    text_horiz_centred(tft, t1, y-20) # yofs[1])
    text_horiz_centred(tft, t2, y+20) # yofs[2])
    text_horiz_centred(tft, t3, y+60) # yofs[2])

    if use_sound:
        play_boot_music()
    time.sleep(2)
    reset_disp(0)
    # show the menu on start
    switch_state(0)
    Stop = False
    s = "Press button 2 to start new game or Y to end"

    while True:
        try:
            if game_state_changed:
                game_state_changed = False

                if game_state == 0:
                    lShown = False
                    lShown2 = False
                    show_menu()
                elif game_state == 1:
                    setup_new_game()
                elif game_state == 3:
                    show_gameover()

            # menu
            if game_state == 0:
                flash_text("PRESS 2") # was: (24, yofs[1], t)
                if not lShown:
                    print(s)
                    lShown = True
                time.sleep(1)
                while True:
                    btn = ck_btns()
                    if btn == 11:
                        print("Ending game...")
                        time.sleep(1)
                        Stop = True
                        break
                    if not (btn == 2):
                        print(s)
                        time.sleep(0.5)
                    else:
                        break
                if Stop:
                    break

            elif game_state == 1:
                draw_snake()

            elif game_state == 3:
                t = "GAME OVER"
                flash_text(t) # was: (34, yofs[1], t)
                if not lShown2:
                    print(t)
                    lShown2 = True

                while True:
                    btn = ck_btns()
                    if btn == 11:  # Y
                        print("Ending game...")
                        time.sleep(1)
                        Stop = True
                        break
                    if not (btn == 2):
                        print(s)
                        time.sleep(1)
                    else:
                        break
                if Stop:
                    break
                switch_state(0) # reset
            handler()
        except KeyboardInterrupt:
            tft.fill(TFT.BLACK)
            time.sleep(2)
            raise SystemExit
    if Stop:
        tft.fill(TFT.BLACK)
        text_horiz_centred( tft, "THE END...", 120 )
        time.sleep(2)
        tft.fill(TFT.BLACK)
        raise SystemExit

if __name__ == '__main__':
    main()