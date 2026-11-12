from pathlib import Path

import pygame as py
from pygame import Vector2 as vect
from pygame.constants import *
from pytmx.util_pygame import load_pygame

import re
from math import atan2, degrees
from os import listdir


SCREENSIZE = (1280, 720)
CENTER = tuple(map(lambda x: x // 2, SCREENSIZE))
ASSETSPATH = Path('Assets')
