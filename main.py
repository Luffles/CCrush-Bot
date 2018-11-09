# https://pillow.readthedocs.io/en/3.1.x/reference/Image.html
from PIL import Image 

# https://pillow.readthedocs.io/en/3.0.x/reference/ImageGrab.html
from PIL import ImageGrab

#some python numbers library
import numpy as np

#a library made for this bot
from sklearn_decoder import ImgRecognizer

#windows mouse/keyboard/file/data interaction
import win32api, win32con

import time

#a library made for this bot that identifies the candy types?
import debug_utils as dbg

#
import simple_solver
import cProfile
import pstats

# Hard coded pixel values?
board_box = (366, 166, 1008, 738)

# Subtracting 1008 from 366, and 738 from 166 to get the total size of the image?
img_size = (board_box[2]-board_box[0], board_box[3]-board_box[1])

# Calculating how big each candy is to know which parts of the screen we want to interact with
# and how many cells there are
cell_size = (img_size[0]/9, img_size[1]/9)

# Now we know how big the cells are, we need to know that it will be 9 in each direction
board_size = 9

# Getting the game board into a useable data structure?
game_board = np.zeros((board_size, board_size), dtype=np.int32)

# Importing an image recognizer library function as 'recognizer'
recognizer = ImgRecognizer()

'''
 candy values:
- 0 blue
- 1 green
- 2 orange
- 3 purple
- 4 red
- 5 yellow
- 6 chocolate'''

# Looks like a list of custom match types
match_list = [(0, 1, 13, 19), (2, 3, 14, 20), (4, 5, 15, 21), (6, 7, 18, 22), (8, 9, 16, 23), (10, 11, 17, 24)]

special_candies = [1, 3, 5, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
simple_candies = [0, 2, 4, 6, 8, 10]
striped_candies_h = [1, 3, 5, 7, 9, 11]
striped_candies_v = range(13, 19)

striped_candies = striped_candies_h[:]
striped_candies.extend(striped_candies_v)

wrapped_candies = range(19, 25)
chocolate = [12]

board_dict = {0: 'blue       ', 1: 's_h_blue   ', 2: 'green      ', 3: 's_h_green  ', 4: 'orange     ', 5: 's_h_orange ',
              6: 'purple     ', 7: 's_h_purple ', 8: 'red        ', 9: 's_h_red    ', 10: 'yellow   ', 11: 's_h_yellow ',
              12: 'chocolate', 13: 's_v_blue   ', 14: 's_v_green  ', 15: 's_v_orange ', 16: 's_v_red    ',
              17: 's_v_yellow ', 18: 's_v_purple ', 19: 'blue_wrapped', 20: 'green_wrapped', 21: 'orange_wrapped',
              22: 'purple_wrapped', 23: 'red_wrapped', 24: 'yellow_wrapped', -1: 'empty    '}

# 3 candies explode for 60 points
# 4 candies exploder for 120 create striped candy - striped candy explodes the whole vertical line
# 5 in a line create a chocolate sprinkle. swipe it with a candy and it explodes candies of that color from the board


# The windows interface, use these coords to click on the screen
def win32_click(x, y):
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

# Calculate the game coords?
def get_desktop_coords(cell):
    x = board_box[0] + cell[1] * cell_size[0] + cell_size[0]/2
    y = board_box[1] + cell[0] * cell_size[1] + cell_size[1]/2
    return x, y

# Actually performing the moves indicated by win32 click and get_desktop_coords
def do_move(move):
    start = move[0]
    end = move[1]

    start_w = get_desktop_coords(start)
    end_w = get_desktop_coords(end)

    win32api.SetCursorPos(start_w)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, start_w[0], start_w[1], 0, 0)
    time.sleep(0.3)
    win32api.SetCursorPos(end_w)
    time.sleep(0.3)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, end_w[0], end_w[1], 0, 0)

    win32api.SetCursorPos((1100, 1100))

# Pulling in the game board to run our functions against
def grab_board():
    global game_board
    img = ImageGrab.grab()

    #img = Image.open('board.bmp')
    img = img.crop(board_box)
    #img.save('board.bmp')
    for y in range(0, 9):
        for x in range(0, 9):
            cell_box = (x*cell_size[0], y*cell_size[1], (x+1)*cell_size[0], (y+1)*cell_size[1])
            cell = img.crop(cell_box)
            #cell.save('Cells/{0}_{1}.bmp'.format(y, x))
            game_board[y][x] = recognizer.predict(cell)

    dbg.print_board(game_board)
    return img

ref_img = None

# board is currently moving, don't do something to it probably?
def board_is_moving():
    global ref_img
    img = ImageGrab.grab()
    img = img.crop(board_box)
    img = img.resize((img.size[0]/4, img.size[1]/4), Image.NEAREST)

    has_movement = True
    if ref_img:
        has_movement = compare_images(img, ref_img, threshold=100) > 100

    ref_img = img
    return has_movement


def are_pixels_equal(p1, p2, threshold):
    diff = 0
    for i in range(3):
        diff += abs(p1[i]-p2[i])
    return diff < threshold


def compare_images(current, reference, threshold):
    current_data = np.array(current.getdata())
    ref_data = np.array(reference.getdata())

    diff_pixels = 0
    total_size = current.size[0]*current.size[1]
    for i in range(0, total_size-3, 3):
        if not are_pixels_equal(current_data[i], ref_data[i], threshold):
            diff_pixels += 1

    print diff_pixels
    return diff_pixels


background_img = Image.open('background.bmp')
background_img = background_img.resize((background_img.size[0]/4, background_img.size[1]/4), Image.NEAREST)

# The actual bits that make all the above code run.  When this file is run, main(): is what is initialized.
def main():
    #Uses the machine learning recognizer data set to train itself?
    recognizer.train()
    #Makes the solver engine available to use as an easy variable below
    solver = simple_solver.SimpleSolver()
    #Tells us when we've won
    img_end_game = Image.open('end_screen.bmp')
    #Slices off some portion of the end game screen to make it useable
    img_end_game = img_end_game.resize((img_end_game.size[0]/4, img_end_game.size[1]/4), Image.NEAREST)
    #Setting a variable to show us total moves
    total_moves = 0
    #While true indicates that it should run until we reach something that tells us it shouldn't
    while True:
        #This is the main internal loop. AKA we're now using data to do stuff.
        #Don't do these things while the board is moving
        if not board_is_moving():
            #Get the board state into an easy to use variable
            board_img = grab_board()
            #Slicing off the game board state to compare against the end game board state to see if we've won
            board_img = board_img.resize((board_img.size[0]/4, board_img.size[1]/4), Image.NEAREST)
            if compare_images(board_img, img_end_game, 10) < 3000:
                break
            #This is left as an exercise to the reader -- what is solver.solve_board(game_board) returning?
            score, move = solver.solve_board(game_board)
            #logging data to the console
            print '\nBest move found. Score = {0}, Move = {1}'.format(score, move)
            #actually performing the 'best move'
            do_move(move)
            #incrementing the move counter
            total_moves += 1
        #Wait before we return to the first statement inside 'while True:'
        time.sleep(0.4)
    print 'Total moves done: ' + str(total_moves)

#Python best practice to run the main function when called from the python interpreter
if __name__ == '__main__':
    main()
    #cProfile.run('main()', filename='stats.txt')
    #stats = pstats.Stats('stats.txt').sort_stats('cumulative')
    #stats.print_stats()

    #recognizer.train()
