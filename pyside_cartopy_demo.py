import sys

from netCDF4 import Dataset
import numpy as np

from PySide2.QtCore import Qt, Slot
from  PySide2.QtWidgets import QMainWindow, QApplication, QWidget, QTableWidget, QComboBox, QLabel, QSlider, QDial, QVBoxLayout, QHBoxLayout

import matplotlib 
#qt painter to draw?

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg 
from matplotlib.figure import Figure

from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator


import cartopy
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

import cmocean


from math import floor

matplotlib.use("Qt5Agg")


class CartopyCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, proj = ccrs.PlateCarree(), width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(1, 1, 1, projection=proj) 
   
        minlon, maxlon, minlat, maxlat = (10, 17.75, 66, 70.24)
        #minlon, maxlon, minlat, maxlat = (20, 40, 66, 70.24)
        proj = ccrs.PlateCarree()
        self.axes.set_extent([minlon, maxlon, minlat, maxlat], crs=proj)
        self.axes.coastlines()
        
        self.axes.plot(13.581, 68.29, marker='o', color='red', markersize=10, alpha=0.7, transform=ccrs.Geodetic())
        #tutaj
        
        self.dataset = Dataset('/home/anna/annaCode/hackathon_2021/data/mfwamglocep_2021040900_R20210407.nc', 'r')
        self.lons = self.dataset.variables['longitude'][:]
        self.lats = self.dataset.variables['latitude'][:]
        self.time_data = self.dataset.variables['time'][:]
        
       
        gr = self.axes.gridlines(draw_labels = True)
        gr.right_labels = False
        
        self.cmap = cmocean.cm.tempo
        (self.w_min, self.w_max) = self.get_min_max(self.dataset)
        self.cb_ticks,self.cb_labels = self.make_ticks(self.w_min, self.w_max)
   
        self.levels = MaxNLocator(nbins=20).tick_values(self.w_min, self.w_max)
        self.norm = BoundaryNorm(self.levels, ncolors=self.cmap.N, clip=True)
        self.dx, self.dy = 0.05, 0.05  
        
        img = self.draw_waves('VHM0_SW1')
        cbar = self.fig.colorbar(img, ax=self.axes, ticks = self.cb_ticks)
        cbar.ax.set_yticklabels(self.cb_labels)
        
        super().__init__(self.fig)
        
    def get_min_max(self, dataset):
        wave_list = ['VHM0_WW', 'VHM0_SW1', 'VHM0_SW2']
        wave_min, wave_max = 0, 0
        for wave in wave_list:
            wave_data = dataset.variables[wave][0, :, :]
            temp_min = wave_data.min()
            temp_max = wave_data.max()
            if temp_min < wave_min:
                wave_min = temp_min
            if temp_max > wave_max:
                wave_max = temp_max
        return (wave_min, wave_max)
        
    def draw_waves(self, wave_type, time_index = 0):
        wave_ti = self.dataset.variables[wave_type][time_index, :, :] #double check how much data i pass, becaue i might maybe limit it by lat and lot
        
        contour_img = self.axes.contourf(self.lons + self.dx/2., self.lats + self.dy/2.,wave_ti, levels=self.levels, cmap=self.cmap)
        return contour_img
        
    def make_ticks(self, w_min, w_max):
        scale = w_max - w_min
        if scale > 10:
            num = floor((w_max - w_min)/2) + 1
        else:
            num = floor(w_max) + 1
        ticks = np.linspace(floor(w_min), floor(w_max), num=num, dtype = int)
        labels = []
        for t in ticks:
            if t == 0:
                labels.append('flat')
            elif t == 1:
                labels.append('1 meter')
            else:
                labels.append(str(t)+ ' meters')
        return ticks, labels
        
        
        
class ApplicationWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self._main = QWidget()
        self.setCentralWidget(self._main)
        
        
        
        #left side controls
        #self.canvas = CartopyCanvas(self.fig)
        self.canvas = CartopyCanvas()
      #  self.canvas.draw_waves('VHM0_SW1')
        self.canvas.mpl_connect("button_release_event", self.on_click)

        #3:00, 6:00, 9:00, 12:00, 15:00 18:00 21:00 00:00
        self.slider = QSlider(minimum=0, maximum=8, orientation=Qt.Horizontal)
        #self.dial = QDial()
        #self.dial.setRange(0, 7)
        #self.dial.setSingleStep(1)
        #widget = QSlider()
        #widget.setMinimum(-10)

        
        # Left layout
        llayout = QVBoxLayout()
        llayout.setContentsMargins(1, 1, 1, 1)
        llayout.addWidget(self.canvas, 88)
        llayout.addWidget(QLabel("time and date:"), 1)
        llayout.addWidget(self.slider, 1)
        
        
        #right side controls
        # Table (Right)
        self.table = QTableWidget()
        # ComboBox (Right)
        self.combo = QComboBox()
        self.combo.addItems(["Primary swell", "Secondary swell", "Wind swell"])
        
        
        # Right layout
        rlayout = QVBoxLayout()
        rlayout.setContentsMargins(1, 1, 1, 1)
        rlayout.addWidget(QLabel("Wave type:"))
        rlayout.addWidget(self.combo)
        rlayout.addWidget(self.table)
        
        
         # Main layout
        layout = QHBoxLayout(self._main)
        layout.addLayout(llayout, 70)
        layout.addLayout(rlayout, 30)
        
        self.combo.currentTextChanged.connect(self.combo_option)
        self.slider.valueChanged.connect(self.slider_changed)
    
    
    @Slot()
    def combo_option(self, text):
        if text == "Primary swell":
            self.canvas.draw_waves('VHM0_SW1')
            self.canvas.draw()
            #self.plot_wire()
        elif text == "Secondary swell":
            self.canvas.draw_waves('VHM0_SW2')
            self.canvas.draw()
            #self.plot_surface()
        elif text == "Wind swell":
            self.canvas.draw_waves('VHM0_WW')
            self.canvas.draw()
            #self.plot_triangular_surface()
    
    @Slot()
    def slider_changed(self, i):
        self.canvas.draw_waves('VHM0_SW1',i)
        self.canvas.draw()
        print(i)
      
    def on_click(self, event):
        #print("tralala")
        if 421 <= event.x <= 431:
            if 318 <= event.y <= 322:
                print("yes!!")
        else:
            print("x")
            print(event.x)
            print(event.y)
            #print(dir(event))
        
#        ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_update_enter_leave', 'button', 'canvas', 'dblclick', 'guiEvent', 'inaxes', 'key', 'lastevent', 'name', 'step', 'x', 'xdata', 'y', 'ydata']

        
       
        
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ApplicationWindow()
    w.setFixedSize(1280, 720)
    w.show()
    app.exec_()        
    
