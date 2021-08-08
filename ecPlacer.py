from typing import Tuple
import cv2
import numpy as np

(screen_width,screen_height) = (1920,1080)
cameras_ids = [1,2]
windowname = "ecPlacer"

class camera:
    def __init__(self,vc,f) -> None:
        self.vc = vc
        self.crop = (0,0)
        self._offset = (30,30)
        self._zoom = False
        self.sel=False
        self.fr = f

    def release(self):
        self.vc.release()

    @property
    def zoom(self)->bool:
        return self._zoom
    
    @zoom.setter
    def zoom(self,b:bool):
        self._zoom=b

    @property
    def selected(self)->bool:
        return self.sel
    
    @selected.setter
    def selected(self,b:bool):
        self.sel=b

    @property
    def offset(self)->bool:
        return self._offset
    
    @offset.setter
    def offset(self,o):
        self._offset = o

    @property
    def cropsize(self)->Tuple:
        return self.crop

    @cropsize.setter
    def cropsize(self,sz:Tuple):
        w,h = sz
        w = (min(w,self.fr.shape[1])>> 1) << 1 # make multiple of 2
        h = (min(h,self.fr.shape[0])>> 1) << 1 
        self.crop = (w,h)

    def read(self):
        rval, img = self.vc.read()
        
        if rval:            
            h,w,_ = img.shape

            div = 2 if self._zoom else 1

            target_size = self.crop
            center = np.round(np.add((w/2,h/2), self.offset))

            top_left =  np.int0(np.subtract(center, np.divide(target_size,div<<1)))  # Center - half size
            bot_right = np.int0(np.add(top_left, np.divide(target_size,div)))        # TopLeft + size

            cropped = img[top_left[1]:bot_right[1],top_left[0]:bot_right[0]]

            if self._zoom:
                cropped = cv2.resize(cropped, target_size , interpolation = cv2.INTER_AREA)

            # Crosshair           
            cv2.line(cropped,(0,target_size[1]>>1),(target_size[0],target_size[1]>>1),(0,255,0),thickness=1)
            cv2.line(cropped,(target_size[0]>>1,0),(target_size[0]>>1,target_size[1]),(0,255,0),thickness=1)

            # Border
            if self.sel:
                cv2.rectangle(cropped,(3,3),np.subtract(target_size,3),(0,0,255),thickness=3)

            return cropped
        else:
            return None


# Mouse Event 
def onMouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        pass

    elif event == cv2.EVENT_RBUTTONDOWN:
        pass
   
cv2.namedWindow(windowname) 
cv2.setMouseCallback(windowname, onMouse)


cameras=[]
# Camera Handles
for c in cameras_ids:
    vc = cv2.VideoCapture(c)
    if vc.isOpened():
       vc.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)  # Go for max 
       vc.set(cv2.CAP_PROP_FRAME_HEIGHT, 1440)
       rval, frame = vc.read()

       if rval:
           cameras.append( camera(vc,frame))

    else:
       rval  = False
    
# Determine the frame size according to the screen size
w = int(screen_width/len(cameras))
for c in cameras:
    c.cropsize = (w,screen_height)

sel = len(cameras) # The selected window (last camera + 1 == none)
frames = len(cameras)*[0] # Init empty frames
while True:
    for idx,c in enumerate(cameras):
        frames[idx]=c.read()
    
    all = np.concatenate(frames, axis=1)
    cv2.imshow(windowname, all)
    
    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break
    elif key == ord('s'): # Select camera
        sel = sel+1 if sel < len(cameras) else 0 
        for idx,c in enumerate(cameras):
            c.selected = (sel == idx)
    # elif key == ord('f'): # Toggle Full Screen 
    #     if cv2.getWindowProperty(windowname,cv2.WND_PROP_FULLSCREEN) == cv2.WINDOW_FULLSCREEN: 
    #         cv2.setWindowProperty(windowname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
    #     else: 
    #         cv2.setWindowProperty(windowname, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    elif key == ord('z'): # Zoom  
        if sel < len(cameras):
            cameras[sel].zoom = not cameras[sel].zoom 

    elif key in range(0,4): #arrows
        #  up: 0, down: 1, left: 2, right: 3
        if sel < len(cameras):
            mov = (1 if key==3 else -1 if key==2 else 0, 1 if key==0 else -1 if key==1 else 0)
            cameras[sel].offset = np.add(cameras[sel].offset,mov)

cv2.destroyWindow(windowname)

for c in cameras:
    c.release()
cv2.destroyAllWindows()
