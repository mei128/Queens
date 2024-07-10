# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 12:11:43 2024

@author: mei256

The Queens by Linkedin game is their property, but this code is free,
just respect the licenses of the modeules used.
"""

from PIL import Image, ImageGrab, ImageDraw
import pyautogui
import numpy as np
import time

#
#   solve
#      cpos : list of lists of cell positions per color
#      locs : array with queens and locked-out positions
#
#   Recursively solve the board by expanding a solution tree,
#   one color per level, crop dead-ends by cutting recursion
#   and back-tracing. 
#
def solve(cpos,locs):
    if len(cpos)==0:                           # If no colors left we are done
        return True
    else:
        for pos in cpos[0] :                   # For all positions of first color in list
            if locs[pos[0],pos[1]]==0 :        #     If unused
                nocs = locs.copy()
                place(pos,nocs)                #        place Queen
                if solve(cpos[1:],nocs) :      #        and solve for remaining colors
                    locs[:] = nocs             #        passing back solution if solved
                    return True
    return False

#
#   place
#      pos  : position tuple (row,col)
#      locs : array with queens and locked-out positions
#
#   Place Queen in the given position, mark locked-out positions.
#   Locs board modified by reference
#
def place(pos,locs):
    size = locs.shape[0]
    locs[pos[0],pos[1]] = 1                      # Mark given position
    for n in range(size):                        # Lock out same row and column
        if locs[pos[0],n] == 0 :
            locs[pos[0],n] = -1
        if locs[n,pos[1]] == 0 :
            locs[n,pos[1]] = -1
    for r in [-1, 1]:                            # Corners, taking care of edges
        cr = 0 if pos[0]+r<0 else size-1 if pos[0]+r>size-1 else pos[0]+r
        for c in [-1, 1]:
            cc = 0 if pos[1]+c<0 else size-1 if pos[1]+c>size-1 else pos[1]+c
            if locs[cr,cc]==0 :
                locs[cr,cc] = -1
    return
#
#   cropboard
#
#   Detect board edges and return image cropped to exact board size
#   and coordinates of board's top left corner. Assumes board is
#   somewhat centered on the screen, covering the mid point, and
#   background color is nearly white.
#
def cropboard():
    screen = pyautogui.screenshot()      # Take screen shot
    screen = screen.convert(mode="RGB")
    sx, sy = screen.size
    mx = sx//2                           # Mid point H
    hx = mx                            
    lx = mx
    my = sy//2                           # Mid point V
    hy = my
    ly = my
    bg = 740                             # bg (empiric)

    while sum(screen.getpixel((lx,my)))<bg :    # Move cursor left until BG
        lx -= 1
        assert lx>0, "Board not found."         #    or limit reached
        
    while sum(screen.getpixel((hx,my)))<bg :    # Move cursor right until BG
        hx += 1
        assert hx<sx, "Board not found."        #    or limit reached
        
    while sum(screen.getpixel((mx,ly)))<bg :    # Move cursor up until BG
        ly -= 1
        assert ly>0, "Board not found."         #    or limit reached
        
    while sum(screen.getpixel((mx,hy)))<bg :    # Move cursor down until BG
        hy += 1
        assert hy<sy, "Board not found."        #    or limit reached

    lx += 1                                     # Step back to edge
    ly += 1

    board = screen.crop([lx,ly,hx,hy])          # Crop board found

    sx, sy = board.size 
    ImageDraw.floodfill(board,(0,0),(0,0,0),50)          # Fill corners (needed?)
    ImageDraw.floodfill(board,(0,sy-1),(0,0,0),50)
    ImageDraw.floodfill(board,(sx-1,0),(0,0,0),50)
    ImageDraw.floodfill(board,(sx-1,sy-1),(0,0,0),50)
    
    return lx, ly, board    # Return top left coords and board image

#
#   gridcount
#
#      img : cropped board image
#
#   Count the number of columns and rows. Just in case,
#   do both vertical directions (some times colors...)
#
def gridcount(img):
    npimg  = np.array(img.convert("L")) # Convert to grayscale array
    npimg[npimg> 100] = 255             # Binary threshold
    npimg[npimg<=100] = 0

    sx, sy = npimg.shape
    cntx = 0                          # Vertical count (array, not image!)
    cnty = 0                          # Horizontal count
    trun = 20                         # Threshold of color runs
    runc = 0
    while cntx==0:                        # Repeat until midline not black
        my = np.random.randint(10,sy-20)  # Random midpoint
        for x in range(sx):               # Move vertical
            if npimg[x,my] :              # Color found
                runc += 1                 #    Increase run count
            else :                        # Black line found
                if runc>=trun :           #    Last color run over threshold?
                    cntx += 1             #        Then we have a square
                runc = 0                  #    Reset count
    runc = 0
    while cnty==0:                        # Repeat until midline not black
        mx = np.random.randint(10,sx-20)  # Random midpoint
        for y in range(sy):               # Move horizontal
            if npimg[mx,y] :              # Color found
                runc += 1                 #    Increase run count
            else :                        # Black line found
                if runc>=trun :           #    Last color run over threshold?
                    cnty += 1             #        Then we have a square
                runc = 0                  #    Reset count
                
    return max(cntx,cnty)

#
#   codeboard
#
#      img : board image cropped
#
#   Code board as an array, with each color represented
#   by a color index (value not relevant). Only used to
#   build the list of square positions per color.
#
def codeboard(img):
    sx, sy = img.size

    cnt = gridcount(img)
        
    # Identify solid colors and discard color compression artifacts:
    colors = img.getcolors(maxcolors=10000)                                  # Get pixel count per color (overkill limit)
    colors.sort(key=lambda x:1e10 if sum(x[1])==0 else x[0], reverse=True)   # Sort in descending order, keep black first
    colors = colors[:cnt+1]                                                  # Keep "solid" colors (most frequent)
    colors = colors[1:]                                                      # Drop black
    cdict  = dict()
    for i in range(len(colors)):    # Color dictionary
        cdict[colors[i][1]] = i     #    Code each RGB with an index
    cdict[(0,0,0)] = cnt            #    Recover black with code = color count

    sqr = sx//cnt                                          # Aprox. square size

    cbrd = np.zeros((cnt,cnt),dtype=np.int8)               # Empty colors board

    for r in range(cnt):                                   # For each row
        sy = sqr//2+r*sqr                                  # 
        for c in range(cnt):                               # and each column
            sx = sqr//2+c*sqr                              #     get approx midpoint
            ix = 1
            cc = -1
            while cc==-1 :                                 # While we don't get a recognized color (compression artifacts get in the middle)
                sx += ix                                   #    shift sample point one pixel
                cc = cdict.get(img.getpixel((sx,sy)),-1)   #    and sample again
                if cc == cnt :                             #    if reached the edge of the square revert shift direction
                    sx -=  ix
                    ix  = -ix
                    cnt = -1
            cbrd[r,c] = cc                                 # Assign color code for current row and column to board representation
            
    return cbrd

#
#   colorlists
#
#      board : color coded board array
#
#   Create list of lists of squares per color, sorted by the number of squares of each color.
#   Pruning dead-ends is more efficient starting by the color with the least square count.
#
def colorlists(board):
    size = board.shape[0]
    cpos = [[] for n in range(size)]             # List of empty lists, one per color
    for r in range(size):                        # For all rows
        for c in range(size):                    #     For all columns
            cpos[board[r,c]].append((r,c))       #         add square position to color list

    cpos.sort(key=lambda x:len(x))               # Sort list by number of squares of each color
    return cpos

#
#   solution
#
#      locs : board with final positions
#      pos  : tuple with top left coords of board
#      img  : board image cropped
#
#   "Clicks" solution on the original board image.
#
def solution(locs,pos,img):
    cnt = locs.shape[0]              # row-col count
    sqr = img.size[0]/cnt            # approx square size
    cr  = sqr//3                     # radius for marker
    drw = ImageDraw.Draw(img)        # drawing object
    for r in range(cnt):
        for c in range(cnt):
            if locs[r,c]==1 :
                cy = round(sqr/2+sqr*r)     # approx square center
                cx = round(sqr/2+sqr*c)
                pyautogui.click(x=pos[0]+cx, y=pos[1]+cy, clicks=2, interval=0.1)  # Click solution on screen
                drw.ellipse([cx-cr,cy-cr,cx+cr,cy+cr], fill=(0,0,0))               # and mark on board
    return

############################################################################
#
# main
#
############################################################################
if __name__ == '__main__' :
    print("""

'Queens by Linkedin' Solver

Have your game ready to start, enter below a number of seconds to give
you time to switch screens and put your Linkedin screen on top, with the
game board somewaht centered, so it covers the center of the screen,
and let the script solve it for you (yeah, it's cheating, but I'm sure
many of those who solve it in seconds everyday also cheat).

          """)
    delay = int(input("Enter number of seconds of delay:"))
    time.sleep(delay)
    crp = cropboard()            # Grab board from the screen

    if crp == None :             # Cropping failed to detect board
        raise Exception("Cannot detect board - verify your layout.")
    else :
        tx, ty, img = crp        # Board coordinates and image
        if abs(1-img.size[0]/img.size[1])>0.02 :
            print(1-img.size[0]/img.size[1],img.size)
            img.show()
            raise Exception("Wrong shape detected - verify your layout.")

    cbrd = codeboard(img)                       # Color coded board 
    cpos = colorlists(cbrd)                     # Color position lists
    locs  = np.zeros(cbrd.shape, dtype=np.int8) # initial empty board

    if solve(cpos,locs):                        # If solution can be found
        solution(locs, (tx,ty), img)            #    play it
        img.show()                              #    and show it
    else:
        print("Problem has no solution (has it?)")