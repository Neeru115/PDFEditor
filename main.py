#!/usr/bin/env python3
"""
PDFEditor - A Kivy-based Android PDF Editor Application
Optimized for Moto G54 5G (8GB RAM, 128GB ROM, Android OS)
Features: PDF viewing, editing, page deletion, and creation
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List

# Kivy imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
