"""
   The contents of this file taken out of main.py (snake game)
   to have this Snake class in a separate file
   Following mods by @PaulskPt (2022-08-22):
   - Added functions:
     set_snake_dims()
     get_snake_dims()
     set_fruit_dims()
     get_fruit_dims()
     is_ate_fruit()
   - added global variable:
     my_debug               to control printing to REPL
   - added variables:
     self._ate_fruit
     self._x
     self._y
     self._s_dims           set to (4, 4)
     self._f_dims           set to (6, 6)
   - added params dw, dh in __init__()
   - mods in function move()
       Setting flag self._ate_fruit when snake ate a fruit (hit)
       xy_extra = 1 value to increase the area in which the fruit can be eaten (hit)
       change the hit equation (if hx >= fx-xy_extra and hx <= fx+self._f_dims[0]+xy_extra and hy >= fy-xy_extra and hy <= fy+self._f_dims[1]+xy_extra:)
       
    LICENSE: See attached LICENSE file
"""
import random, math
my_debug = False

class Snake:
    def reset(self, x, y, len, dir):
        self._moves = 0
        self._dead = False
        self._ate_fruit = False
        self._length = len
        self._dir = 0
        self._speed = 0.12
        self._score = 0
        self._fruit = []
        self._x = x  # added by @Paulskpt
        self._y = y  # idem
        self._s_dims = (6, 6) # idem
        self._f_dims = (8, 8) # idem
        if my_debug:
            print("Snake starts at position hor: {}, vert: {}, length: {}, direction: {}".format(self._x, self._y, len, dir))
        # set snake head position
        self._list = [ [self._x, self._y] ]
        # dynamically create snake body based on starting position
        for i in range( self._length-1 ):

            if self._dir == 0:
                self._y += 2
            elif self._dir == 1:
                self._x -= 2
            elif self._dir == 2:
                self._y -= 2
            elif self._dir == 3:
                self._x += 2
            
            self._list.append( [self._x, self._y] )
        
        self.add_fruit()

    # Parameters dw and dh added by @PaulskPt
    def __init__(self, dw, dh, x, y, len, dir):
        self._dw = dw  # display width
        self._dh = dh  # display height
        self.reset( x, y, len, dir )

    # added by @PaulskPt
    def set_snake_dims(self, aDims):
        s_dims_dflt = (6, 6)
        s_dims_ok = False
        if type(aDims) is tuple:
            if len(aDims) == 2:
                s_dims_ok = True
                self._s_dims = aDims
        if not s_dims_ok:
            self.s_dims = s_dims_dflt
            
    # added by @PaulskPt
    def get_snake_dims(self):
        return (self._s_dims)
            
    # added by @PaulskPt
    def set_fruit_dims(self, aDims):
        f_dims_dflt = (8, 8)
        f_dims_ok = False
        if type(aDims) is tuple:
            if len(aDims) == 2:
                f_dims_ok = True
                self._f_dims = aDims
        if not f_dims_ok:
            self.f_dims = f_dims_dflt
            
    # added by @PaulskPt
    def get_fruit_dims(self):
        return (self._f_dims)
    
    # added by @PaulskPt
    # This flag state can be used by the calling program
    # to play a sound upon the snake ate a fruit
    # The flag is reset in reset() and in move()
    # and is set in move()
    def is_ate_fruit(self):
        return self._ate_fruit

    def set_dir(self, dir):
        # Chnage directiom
        # 0 = UP, 1 = RT, 2 = DN, 3 = LT
        """
        if dir == 0
            self._dir -= 1
        elif dir == 1
            self._dir += 1

        # Wrap direction
        if self._dir < 0:
            self._dir = 3
        elif self._dir > 3:
            self. _dir = 0
        """
        self._dir = dir
        
    def move(self):
        TAG = "Snake::move(): "
        self._ate_fruit = False # reset flag
        xy_extra = 1 # increase the area in which the fruit can be eaten (hit)
        
        # Increase snake length every 10 moves
        # self._moves += 1
        # if self._moves == 10:
        #     self._moves = 0
        #     self._length += 1
        if self._dh > self._dw:  # if the height > width then reverse their values
            t = self._dw
            self._dw = self._dh
            self._dh = t
            print(TAG+"dimensions after being reversed: dw, dh = ", self._dw, self._dh)
        else:
            if my_debug:
                print(TAG+"dw, dh = ", self._dw, self._dh)
        remove_tail = [0,0,0,0]
        # renamed x,y into tx,ty to signify tail (mod by @Paulskpt)
        if len( self._list ) == self._length:
            tx,ty = self._list[ self._length-1 ]
            remove_tail[0] = tx
            remove_tail[1] = ty
            del self._list[ self._length-1 ]

        # renamed x,y into hx,hy to signify head (mod by @Paulskpt)
        # Grab the x,y of the head
        hx, hy = self._list[0]

        # move the head based on the current direction
        if self._dir == 0:
            hy -= 2
        elif self._dir == 1:
            hx += 2
        elif self._dir == 2:
            hy += 2
        elif self._dir == 3:
            hx -= 2
            
        # ul = upper-left
        # lr = lower-right
        ul = (0, 0) 
        lr = (self._dw, self._dh)
        
        # Did we hit the outer bounds of the level?
        #hit_bounds = self._x < 1 or self._y < 1 or self._x > 125 or self._y > 61
        #hit_bounds = hx < 1 or hy < 1 or hx > self._dw-1 or hy > self._dh-1
        hit_bounds = hx < ul[0] or hy < ul[1] or hx > lr[0] or hy > lr[1]

        # Is the x,y position already in the list? If so, we hit ourselves and died - we also died if we hit the edge of the level 
        self._dead = self._list.count( [hx, hy] ) > 0 or hit_bounds

        # Add the next position as the head of the snake
        self._list.insert( 0, [hx, hy] )

        # Did we eat any fruit?
        for f in self._fruit:
            fx,fy = f
            
            #  xy_    f.............f xy_
            #  extra  x.............x extra 
            #  (n)    0.............7 (n)
            #-+-----------------------------+-------------
            #   .    [...............] .      xy_extra (n)
            #   .     + + + + + + + +  .      fy0        ASSUMING THE DEFAULT FRUIT DIMENSION = (8, 8)
            #   .     + + + + + + + +  .      fy1
            #   .     + + + + + + + +  .      fy2        THIS IS THE 'TOUCH' AREA OF THE FRUIT OBJECT
            #   .     + + + + + + + +  .      fy3
            #   .     + + + + + + + +  .      fy4        Hor:  from the fruit x-value - xy-extra until the fruit x-value + xy_extra
            #   .     + + + + + + + +  .      fy5
            #   .     + + + + + + + +  .      fy6        Vert: from the fruit y-value - xy-extra until the fruit y-value + xy_extra
            #   .     + + + + + + + +  .      fy7
            #   .    [...............] .      xy_extra (n)
            #-+-----------------------------+--------------
            
            if my_debug:
                print(TAG+"snake area= ({:03d},{:03d})-({:03d},{:03d})".format(hx, hy, hx + self._s_dims[0], hy + self._s_dims[1]))
                print(TAG+"fruit area= ({:03d},{:03d})-({:03d},{:03d})".format(fx, fy, fx + self._f_dims[0], fy + self._f_dims[1]))

            if hx >= fx-xy_extra and hx <= fx+self._f_dims[0]+xy_extra and hy >= fy-xy_extra and hy <= fy+self._f_dims[1]+xy_extra:
                print("snake ate a fruit !!!")
                self._ate_fruit = True
                remove_tail[2] = fx
                remove_tail[3] = fy
                self.eat_food()
                self._fruit.remove( f )
                self.add_fruit()

        return remove_tail

    def is_dead(self):
        return self._dead

    def get_positions(self):
        return self._list

    def get_speed(self):
        return self._speed

    def get_score(self):
        return self._score

    def eat_food(self):
        self._score += 1
        self._length += 2
        # reduce the speed time delay, burt clamped between 0.05 and 0.12
        self._speed = max(0.01, min( self._speed - 0.01, 0.12))

        # print("Score {}, Speed {}".format( self._score, self._speed))

    def add_fruit(self):
        fx = random.randrange(5,self._dw-5) #* 2  # was (2, 60) * 2
        fy = random.randrange(5,self._dh-5) #* 2  # was:(2, 30) * 2
        self._fruit.append( (fx, fy) )

    def get_fruit_positions(self):
        return self._fruit