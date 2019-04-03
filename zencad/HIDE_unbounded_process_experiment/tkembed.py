import tkinter
import pyservoce
import time
import os

scn = None
winid = None
inited = None
view = None
viewer = None

lastshown = 0


def start_window(scene):
    # global scn
    # global winid
    # scn = scene
    # root = tkinter.Tk()
    ##embed = tkinter.Frame(root, width = 500, height = 500) #creates embed frame for pygame window
    ##embed.grid(columnspan = (600), rowspan = 500) # Adds grid
    ##embed.pack(side = tkinter.LEFT) #packs window to the left
    #
    # winid = root.winfo_id()
    #
    ##button1=tkinter.Button(top,text="Exit")
    ##button1.pack()
    ##embed.bind('<Configure>',showh)
    ##button1.bind('<Button-1>',showh)
    #
    ##viewer = pyservoce.Viewer(scn)
    ##view = viewer.create_view()
    ##view.set_window(winid)
    ##view.set_gradient()
    ##view.redraw()
    #
    ##top.protocol("WM_SHOWWINDOW", showh)
    # root.config(bg="")
    #
    # root.update()
    #
    # viewer = pyservoce.Viewer(scn)
    # view = viewer.create_view()
    # view.set_window(winid)
    # view.set_gradient()
    # view.fit_all()
    # view.redraw()
    #
    # 	#while 1:
    # 	#	pass
    #
    # while True:
    # 	root.update()
    # 	view.must_be_resized()

    root = tkinter.Tk()
    termf = tkinter.Frame(root, height=400, width=500)

    termf.pack(fill=tkinter.BOTH, expand=tkinter.YES)
    wid = termf.winfo_id()
    os.system("xterm -into %d -geometry 80x20 -sb &" % wid)

    root.mainloop()
