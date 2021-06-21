# -*- coding: utf-8 -*-
# author: Robert Molenaar email r.molenaar@utwente.nl
# Release v1.0
# Date 2021 June 21
# To be used on PicoQuant PTU files
# Function: Batchwise multichannel image conversion on Single files an Z stacks.


class Set_Channel_Info:
        
    def __init__(self, Channel, Name, Color, Gain, PIE_TimeGate, FRET_attribute):
        self.Channel        = Channel-1
        self.ChannelName    = 'Ch'+str(Channel)
        self.Name           = Name
        self.Color          = Color
        self.Gain           = Gain
        self.TimeGate       = PIE_TimeGate-1
        self.FRET           = FRET_attribute
        
"""##################  START of user input ###########"""

#TimeGate in PulsedInterlievedExcitation (PIE) is set by PQ hardware, the it starts with the first Laser Model 0->1->2->3 so 640, 560,488 and 405 
#                          Ch,  NameLabel,              Coloring, Gain, PIE TimeGate, FRET
Config1 = Set_Channel_Info(1,   'Alexa 647'    ,   'Red'      ,2      ,1 , '-')
Config2 = Set_Channel_Info(2,   'Alexa488'     ,   'Green'    ,2      ,1 , '-'  )
Config3 = Set_Channel_Info(3,   'Dapi-1     '  ,   'Blue'     ,2      ,2 , 'acceptor')
Config4 = Set_Channel_Info(4,   'Dapi-2'       ,   'Blue'     ,2      ,3 , 'donor')

#File picking
GUI_MultiPick=True      #Pick multiple files - Set Flase to proccess the full folder
Zstack=True             #unlocks the 3D stack options
Default_prompt= r'D:\'  

#Miscellaneous.
Save_data_files=True            #Write CSV data files with intensity of all channels 8.dat
show_gain_on_Images=True        #Shows the gain in the image
shortEndPIEtac=0                #cut a piece from the start TAC ns to supress noise
shortFrontPIEtac=0              #cut a piece from the start TAC ns to surpess noise
PieAutoColor=False              #In PIE mode overwrite colour settings of the channel PIE laser x TimeGate give knowledge of correct color
ShowDefault=True                #Standard user visualizations

#FRET settings     Set 'acceptor' and 'donor' in Config channels and timegates are extracted automatically
FRET=False                      
if FRET ==True:
     Zstack=False
    

#USER specific images
USER_1=False            #optional example: Shows the intensity of the Red channel next to the RGB
USER_2=False            #optional example: image that directly comparee the image with out the Red channel

#Z-stack related
Plot_OrthogonalProjections=True     #Enables orohogonal projections of a Z stack   
Plot_mean_Zplane_Intensity=False    #plot the mean of the channels as function Z
SaveConvertedBin=False              #optional Saves the Binary converted CZ[z,x,y,ch] stack
 
if Plot_OrthogonalProjections==True and Zstack==True:   
    #plane and projections options for the orthogonal Projection
    Plot_mean_Zplane_Intensity=True #optional image to find brightes plane.
    Zplane_threshold=3          #intensity thresholding mean(Zplane)+[n]*stdev (ZPlane)) NOTE!1 set 0 to disable thresholding
    projection='max'            # choose 'max'or 'mean'
    Centerline='ON'
    FlipZ=False             #Flip ortogonal Z plane in the Sub figures, bottom is bottom default use false
    GUI_MultiPick=True
    Vert_centerlineX=128    #Orthogonal projection of rows
    Hor_centerlineY=128     #Orthogonal projection of column
    WidthX=7                #ODD value
    WidthY=7                #ODD value
    StripZ_coverslip=0      #If the Z-Stack is to large, you can strip a few slices
    StripZ_top=0            #If the Z-Stack is to large, you can strip a few slices


"""################## END of user input ###########"""

from readPTU_FLIM import PTUreader
import numpy as np
from ctypes import wintypes, windll
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from functools import cmp_to_key
import os
import getpass
import wx
import time
np.set_printoptions(precision=3)
np.set_printoptions(suppress=False)

SEPIA_laser_lines=[638,560,488,405]      # Set avaialble lasers lines at the SEPIA slot 0,1,2,3
plt.style.use('seaborn-dark')     #  seaborn-dark  https://matplotlib.org/3.1.1/gallery/style_sheets/style_sheets_reference.html


def GUI_select_Multi_file(message):
    """ Function selects one or multiple PTU filenames via a GUI,
        It starts at the current working directory of the process
    """
    wildcard = "picoquant PTU (*.ptu)| *.ptu"
    app = wx.App()
    frame = wx.Frame(None, -1, 'win.py', style=wx.STAY_ON_TOP)
    frame.SetSize(0,0,200,50)
    FilePicker = wx.FileDialog(frame, "Select you PTU files | single or Multiple", defaultDir=Default_prompt, wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST)
    FilePicker.ShowModal()
    FileNames=FilePicker.GetPaths()
    app.Destroy()
    return FileNames

def GUI_select_folder(message):
    """ A function to select a PTU filename via a GUI,
        It starts at the current working directory of the process
    """
    wildcard = "picoquant PTU (*.ptu)| *.ptu"
    app = wx.App()
    path = wx.FileSelector(message='Select you the folder', default_path=Default_prompt, default_extension='*.ptu', wildcard=wildcard)
    directory,filename=os.path.split(path)
    app.Destroy()
    print('Selected file folder: '+path)
    return directory

def winsort(data):
    """ Python indexes files not as windows shows in File explorer this definition reorganises
    """
    _StrCmpLogicalW = windll.Shlwapi.StrCmpLogicalW
    _StrCmpLogicalW.argtypes = [wintypes.LPWSTR, wintypes.LPWSTR]
    _StrCmpLogicalW.restype  = wintypes.INT
    cmp_fnc = lambda psz1, psz2: _StrCmpLogicalW(psz1, psz2)
    return sorted(data, key=cmp_to_key(cmp_fnc))

def Channels_list(data_stack):
    """Function screens all 4 data channels if intensity >0 channel is probably used and pit into the outlist 
    Practical sometime there a countable counts in an image, so intensity need to be larger than the number of lines pixY
    """
    ch=[0,1,2,3]
    CLSch=[Config1,Config2,Config3,Config4]
    out=np.empty(0)
    out2=np.empty(0)
    info= ''
    for i in ch:
      if np.sum(data_stack[:,:,i]) >= ptu_file.head["ImgHdr_PixY"]+5:
          out=np.append(out,CLSch[i])
          info=info+'Ch'+str(i+1)+' '
          out2=np.append(out2,'Ch'+str(i+1))
    print(info+'detected in file: '+f_name)
    print('Image size: '+str(ptu_file.head['ImgHdr_PixX'])+'p x '+str(ptu_file.head['ImgHdr_PixY'])+'p  Objective: '+Read_objective())
    return out, out2

def Read_FRET_Donor_Ch_index(Config):
    """Help function, to read the Donor and Acceptor Channel from the ch_list"""
    
    if len(Config)==1:
        i=1
    
    elif len(Config)>=2:
        i=0
        for h in Config:
            if h.FRET=='donor' or h.FRET=='Donor':
                break
            else:
                 i+=1
    return  i

def Read_FRET_Acceptor_Ch_index(Config):
    """Help function, to read the 'donor' and 'acceptor' Channel from the ch_list"""
    
    if len(Config)==1:
        i=0
    
    elif len(Config)>=2:
        i=0
        for h in Config:
            if h.FRET=='acceptor' or h.FRET=='Acceptor':
                break
            else: 
                i+=1               
                
    return  i
    
def Read_FRET_Donor_TimeGate(Config):
    """Help function, in 2 ch PIE mode mode, TimeGate for fret is always the last one: 
        In the case you have use 3 or 4 cahnnels, including a FRET pair this script reads the Timegate for the donor set in the Config
    it returns the donor and Accpetor"""
    
    if len(Config)==1:
        Donor_TGate=1
        #Acceptor_TGate=0
    
    elif len(Config)>=2:
        for h in Config:
            if h.FRET=='donor' or h.FRET=='Donor':
                 Donor_TGate= h.TimeGate
                 break
    return  Donor_TGate

def Read_FRET_Acceptor_TimeGate(Config):
    """Help function, in 2 ch PIE mode mode, TimeGate for fret is always the last one: 
        In the case you have use 3 or 4 cahnnels, including a FRET pair this script reads the Timegate for the donor set in the Config
    it returns the donor and Accpetor"""
    
    if len(Config)==1:
         #Donor_TGate=1
         Acceptor_TGate=0
    
    elif len(Config)>=2:
        for h in Config:
            if h.FRET=='acceptor' or h.FRET=='Acceptor':
                 Acceptor_TGate= h.TimeGate
                 break
            
    return  Acceptor_TGate 


def Read_SEPIA_laser_lines():
    """This fuction, extracts the used laser lines by reading the intensity from laser (Sep2_SLM_200_FineIntensity)
    if it's 0, it's OFF. 
    Returns an array of used laser lines: used for calulation in TimeGates
    info: string text of laser summary
    Colour_out: an array with sugested color used in AutoColour option    
    """
    atribute=[200,300,400,500]   #names of lasers moduls in ptu headerfile
    color_recommend=['Red','Yellow','Green','Blue']
    out=np.empty(0)
    Colour_out=[]
    info=''
    info2=''
    i=0
    for a in atribute:
        if ptu_file.head["Sep2_SLM_"+str(a)+"_FineIntensity"] !=0:
            out=np.append(out,SEPIA_laser_lines[i])
            Colour_out=np.append(Colour_out,color_recommend[i])
            info2=info2+str(SEPIA_laser_lines[i])+': '+str(ptu_file.head["Sep2_SLM_"+str(a)+"_FineIntensity"])+'% \n'
            if i==0:            
                info=info+str(SEPIA_laser_lines[i])
            else:
                info=info+' + '+str(SEPIA_laser_lines[i])
            i=i+1
        else:
            i=i+1
    print(info2)
    return out,info,Colour_out

def Read_objective():
    """ Extracts the objective setting in symphotime.
    Here you can add the full `name of the lens set in the microscop
    Set your objectives
    If objectives have been defined in Symphotime64 configuration these specific names is passed
    """
    lens=ptu_file.head['ImgHdr_ObjectiveName']    
    if lens =='20x':
        lens=' UCPLFLN20x NA0.6'
    elif lens =='40x':
        lens='  PLN40x NA0.65'
    elif lens =='60x':
        lens='  UPLSAPO60x NA1.2'
    elif lens =='63x':
        lens='  C-planApo63x NA1.4'
    return lens


def Plot_FRET_Histogram(HistoIn,bins,save_fig):
    """Plot a FRET efficiency hsitogram"""

    Data=HistoIn.flatten()
    fig5, ax = plt.subplots()
    plt.title('Histogram of FRET Efficiency \n '+f_name)
    ax.hist(Data[Data !=0], bins=bins)
    ax.set(xlabel='FRET Efficiency', ylabel='count')   # Optionally, label the axes.

    if save_fig is True:
        plt.savefig(d_name+'\\'+f_name+'_FRET_histogram.png', bbox_inches='tight', dpi=150)


def Plot_intesity_image(intensity_im):
    """plots the intensity profile of a time lapse  """
    extent1=[0, ptu_file.head["ImgHdr_PixX"]*ptu_file.head["ImgHdr_PixResol"],0,ptu_file.head["ImgHdr_PixY"]*ptu_file.head["ImgHdr_PixResol"]]
    plt.imshow(intensity_im, extent=extent1)
    plt.title('Raw Intensity image')
    plt.xlabel('X $\mu$m')
    plt.ylabel('Y $\mu$m')
    plt.show()

def Fill_colour(Ch, colour, gain=1,Normed2=0):
    """converts the PTU intensity data int a RGB colour image: normalisation for all channels is done 0:1
    Normalization to an other value is avaialble by passing a vlaue to 'normed2'
    """
    #ColourRGB=np.zeros((ptu_file.head["ImgHdr_PixX"],ptu_file.head["ImgHdr_PixY"],3))
    ColourRGB=np.zeros((Ch.shape[0],Ch.shape[1],3))
    
    if np.max(Ch)<=5: 
           gain=0.01
           print('WARNING: Brightest pixel in the image = '+str(np.max(Ch))+' counts: '+colour+' image is considered as noise and attenuated.')
    if Normed2 != 0:    #Dafault 0 is set  0: If its different the input value is used
        Normed=Normed2
    else:               #otherwise the max value in the channel
        Normed=np.max(Ch)

    if colour=='Blue':
        ColourRGB[:,:,2]=gain*Ch/Normed
    elif colour=='Green':
        ColourRGB[:,:,1]=gain*Ch/Normed
    elif colour=='Red':
        ColourRGB[:,:,0]=gain*Ch/Normed
    elif colour=='Yellow':
        ColourRGB[:,:,0]=gain*Ch/Normed
        ColourRGB[:,:,1]=gain*Ch/Normed
    elif colour=='Orange':
        ColourRGB[:,:,0]=1*gain*Ch/Normed
        ColourRGB[:,:,1]=0.6*gain*Ch/Normed
    elif colour=='Ygreen':
        ColourRGB[:,:,0]=0.4*gain*Ch/Normed
        ColourRGB[:,:,1]=1*gain*Ch/Normed
    elif colour=='Cyan':
        ColourRGB[:,:,1]=gain*Ch/Normed
        ColourRGB[:,:,2]=gain*Ch/Normed
    elif colour=='Magenta':
        ColourRGB[:,:,0]=gain*Ch/Normed
        ColourRGB[:,:,2]=gain*Ch/Normed
    elif colour=='Purple':
        ColourRGB[:,:,0]=0.3*gain*Ch/Normed
        ColourRGB[:,:,2]=gain*Ch/Normed
    return np.clip(ColourRGB,0,1)


path_select=[0]
Errors=['']
Z_Slice=0
#%% 

#Read PTU files SinglePick selects a single file
#Read Z-stack processes all *.ptu files in the folder (typica with a stack)

if GUI_MultiPick==True:
    #single or multiple proccess
    print('Single or Multiple files')
    path_select=GUI_select_Multi_file('Select a file')
    path_select=winsort(path_select) 
else:
    #FUll Folder proccess
    print('Converting all *.ptu images in the folder')
    GUI_MultiPick=False
    path =GUI_select_folder('Select a folder')
    os.listdir(path)
    FileList=[]
    
    i=0
    for file in os.listdir(path):
       i=i+1
       if file.endswith(".ptu"):
            FileList.append(os.path.join(path, file))
    path_select=winsort(FileList)    

#File list now goes into a for loop cycling over the files.

""" ################################################
########         MAIN Proceesing loop       ########
################################################ """

for path in path_select:
    #Main loop that procceses all *.PTU files (path_select) from Multiple file pick or folder
    head, tail = os.path.split(path)
    print('\nConverting TCSPC-data from | '+tail+ ' | to an image.')    
    
    ptu_file  = PTUreader((path), print_header_data = False)
    
    #File checking if its 1D or 2d: skip to next file if 1D
    if ptu_file.head["Measurement_SubMode"] !=  3:
        Errors=np.append(Errors,path)
        print('NOTE: File is a Point-measurement: skip to next *.PTU file')
        continue
        
    #make file and folder names
    os.path.dirname(path)
    d_name, f_name=os.path.split(path)
    f_name, ex=os.path.splitext(f_name)
    d_name=d_name+'\Python_Converted_'+getpass.getuser()+'\\'
    #d_name=d_name+'\Python_converted\\'*f_name
    os.makedirs(d_name,exist_ok=True)
    
    #convert FIFO data into a histogram 4D x,y,channel, hsitodata, returns 4d datastack and intnsity image
    # make a channel list
    
    try:
        # READ PTU data into FLIM data stack
        flim_data_stack, intensity_image = ptu_file.get_flim_data_stack()
    except:
        Errors=np.append(Errors,path)
        print('WARNING: File-ERROR: in RAW to FLIM conversion')
        continue
    
    try:
        # SCREEN for avaialbe Channels
        ch_list, ch_listst=Channels_list(flim_data_stack)
    except:
        Errors=np.append(Errors,path)
        print('WARNING: File-ERROR: in Channel auto-detect')
        continue
    
    
    #extra info
    LaserLines, LaserInfo, ch_color=Read_SEPIA_laser_lines()    
    Objective=Read_objective()
    
    
    #Init a color array 
    CS=np.zeros((ptu_file.head["ImgHdr_PixX"],ptu_file.head["ImgHdr_PixY"],3,len(ch_list)))
    #converts TCSPC into intensity, the importred data is flipped compared with symphotime64, for convievence it is fliplr()
    if Z_Slice==0:
        #make a 3D stack array and read Z positions
        CZ=np.zeros((len(path_select),ptu_file.head["ImgHdr_PixX"],ptu_file.head["ImgHdr_PixY"],len(ch_list)))
        Z_section=np.zeros(len(path_select))
    #array with Z,X,Y,channel,collapedlifetime=intensity #nocolor image only make in the first itteration
    Z_section[Z_Slice]=ptu_file.head['ImgHdr_Z0'] #read Zposition from the header file
    
    if ptu_file.head['UsrPulseCfg'] == 'PIE':
        # Extracting the intensity from PIE timegates into a color channel CS (ColorStack)and data CZ Channel (Cz)
        # extract the deteceted channels (ch_list) from the flim_data_stack and added them in RGB ColorStacs (CS)
        # second add the intensity from this Z-pane into the 3D stack (CZ) Z,X,Y,Ch which is raw intensity for the TimeGate
        
        Excitation='PIE-excitation: '+LaserInfo
        shortEndPIEtac=round(shortEndPIEtac/(ptu_file.head['MeasDesc_Resolution']*1E9)) #ns)
        shortFrontPIEtac=round(shortFrontPIEtac/(ptu_file.head['MeasDesc_Resolution']*1E9)) #ns)
        PieBaseLen=int(np.trunc(len(flim_data_stack[0,0,0])/len(LaserLines)))
        Time_gate_edges=np.zeros((len(LaserLines), 2))
        i=0
        for m in LaserLines:
            Time_gate_edges[i]=(i*PieBaseLen)+shortFrontPIEtac,((i+1)*PieBaseLen-1-shortEndPIEtac)
            i=i+1

        print('PIE TCSPC-TAC-timerange = '+str(round(len(flim_data_stack[0,0,0])*ptu_file.head['MeasDesc_Resolution']*1E9))+'ns \nTime Gates:')
        for j in Time_gate_edges:
            print(j*ptu_file.head['MeasDesc_Resolution']*1E9)
                
        #Push intensity into a normalized [0,1] RGBimage 
        #The detected channels are piut into RGB images stack [x,y,RGB,channels]
        #CS=[len(ch_list)] #channel stack
        i=0
        for l in ch_list:
             
             if FRET==True:
                 Tg=Read_FRET_Donor_TimeGate(ch_list)
                 if i==0:
                     print('Note: FRET-mode: selected TimeGate=Donor '+str(Tg))
             else:
                Tg= l.TimeGate
             if PieAutoColor==True and len(ch_list)==len(LaserLines):
                 FillColor=ch_color[i]
             else:
                 FillColor=l.Color
             try:
                 CS[:,:,:,i]=Fill_colour(np.sum(flim_data_stack[:,:,l.Channel,int(Time_gate_edges[Tg,0]):int(Time_gate_edges[Tg,1])],axis = 2) ,FillColor,l.Gain)
                 CZ[Z_Slice,:,:,i]=np.sum(flim_data_stack[:,:,l.Channel,int(Time_gate_edges[Tg,0]):int(Time_gate_edges[Tg,1])],axis = 2)
             except:
                 Errors=np.append(Errors,path)
                 print('WARNING Script-Error: in Config.TimeGate the PIE-TimeGate incorrect '+l.ChannelName+' is not time gate'+str(l.TimeGate))
                 time.sleep(2)
                 continue
                
            #Filling the arrays for textfile save (actual saving = later)
             if  l.Channel==0:
                 Ch1=np.sum(flim_data_stack[:,:,0,int(Time_gate_edges[Tg,0]):int(Time_gate_edges[Tg,1])],axis = 2) 
             if  l.Channel==1 and Save_data_files==True:
                 Ch2=np.sum(flim_data_stack[:,:,1,int(Time_gate_edges[Tg,0]):int(Time_gate_edges[Tg,1])],axis = 2) 
             if l.Channel ==2 and Save_data_files==True:
                 Ch3=np.sum(flim_data_stack[:,:,2,int(Time_gate_edges[Tg,0]):int(Time_gate_edges[Tg,1])],axis = 2) 
             if  l.Channel==3 and Save_data_files==True:
                 Ch4=np.sum(flim_data_stack[:,:,3,int(Time_gate_edges[Tg,0]):int(Time_gate_edges[Tg,1])],axis = 2) 
             i=i+1   
        #intensity_image=np.fliplr(intensity_image)
    
    
    else:
        
        #standard excitation
        
        ColapsedLT=np.sum(flim_data_stack, axis = 3)
        Excitation='Normal Excitation: '+LaserInfo
        if  Save_data_files==True:
            #Filling the arrays for textfile save (actual saving = later)
            Ch1=ColapsedLT[:,:,0]
            Ch2=ColapsedLT[:,:,1]
            Ch3=ColapsedLT[:,:,2]
            Ch4=ColapsedLT[:,:,3]
        #intensity_image=np.fliplr(intensity_image)

        #Extract the deteceted channels (ch_list) from the flim_data_stack and added them in RGB ColorStacs (CS)
        #Second add the intensity from this Z-pane into the 3D stack (CZ) Z,X,Y,Ch which is raw intensity for the TimeGate
        #Push intensity into a normalized [0,1] RGBimage 
        #The detected channels are put into RGB images stack [x,y,RGB,channels]
        
        i=0
        for l in ch_list:
            CS[:,:,:,i]=Fill_colour(ColapsedLT[:,:,l.Channel],l.Color,l.Gain)
            CZ[Z_Slice,:,:,i]=np.sum(flim_data_stack[:,:,l.Channel,:],axis = 2)
            i=i+1
        
   
    #%%
    #Read some information for in the experimental info headers
    
    timestamp=ptu_file.head["File_CreatingTime"]
    date=timestamp.split(sep=' ')
    DwellTime='Pixel dwell-time: '+'{:04.1f}'.format((ptu_file.head['ImgHdr_TimePerPixel']*1000))+'$\mu$s'
    extent=[0, ptu_file.head["ImgHdr_PixX"]*ptu_file.head["ImgHdr_PixResol"],ptu_file.head["ImgHdr_PixY"]*ptu_file.head["ImgHdr_PixResol"],0]
   
    """ ###########################################################
    ############     Images are plotted from here      ############
    ###########################################################"""
   
    
   
    
    """plot 1 figure color image based by 1 channel"""
    
    if len(ch_list)==1 and ShowDefault==True:
        print('plot reference #1')
        Chinfo1=ch_list[0]
        fig2, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
        rect = fig2.patch  #modify background color
        rect.set_facecolor('whitesmoke')
        #fig2.suptitle('- PicoQuant MT200 -', fontsize=14, weight='bold')
        plt.figtext(0.125,0.925,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.9,'Date: '+date[0]+'     '+Excitation+Objective)
        plt.figtext(0.126,0.88, DwellTime)
        im1 = axs[0].imshow(intensity_image, cmap='gray', extent=extent)
        axs[0].set_title('Intensity', size=12)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        cbar=fig2.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label('Intensity counts', labelpad=8, rotation=90)
        
        im2 = axs[1].imshow(CS[:,:,:,0], extent=extent)
        if ch_list[0].Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.58,0.16,'bright gain:'+str(ch_list[0].Gain), color='whitesmoke')
        axs[1].set_title(ch_list[0].ChannelName+':  '+ch_list[0].Name, size=12)
        axs[1].set_xlabel('X $\mu$m')
        axs[1].set_ylabel('Y $\mu$m')
        
        plt.savefig(d_name+'\\'+f_name+'_Intensity_1ch.png',dpi=300)
        plt.show()
   
    
    """plot2 figure color image based by 2 channels"""  
        
    if len(ch_list)==2 and ShowDefault==True  and FRET==False:
        print('plot reference #2')

        fig, axs = plt.subplots(2, 2, figsize=(14, 12))
        rect = fig.patch  #modify background color
        rect.set_facecolor('whitesmoke')
        #fig.suptitle('- PicoQuant MT200 -', fontsize=14, weight='bold')
        plt.figtext(0.125,0.94,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.925,'Date: '+date[0]+'     '+Excitation+Objective)
        plt.figtext(0.126,0.91, DwellTime)
        
        im1 = axs[0, 0].imshow(intensity_image, cmap='gray', extent=extent)
        axs[0,0].set_title('Combined intensity', size=12)
        axs[0,0].set_xlabel('X $\mu$m')
        axs[0,0].set_ylabel('Y $\mu$m')
        cbar=fig.colorbar(im1, ax=axs[0, 0], fraction=0.065, pad=0.02)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label('Intensity counts', labelpad=8, rotation=90)
        
        im2 = axs[0, 1].imshow(CS[:,:,:,0]+CS[:,:,:,1], extent=extent)
        if ch_list[0].Gain * ch_list[1].Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.585,0.54,'Brightness:'+str(ch_list[1].Color+str(ch_list[1].Gain)+'x '+str(ch_list[0].Color)+' '+str(ch_list[0].Gain)+'x', color='whitesmoke'))
        axs[0,1].set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[1].Color+': '+ch_list[1].Name, size=12)
        axs[0,1].set_xlabel('X $\mu$m')
        axs[0,1].set_ylabel('Y $\mu$m')
        
        im3 = axs[1, 1].imshow(CS[:,:,:,0], extent=extent)
        if ch_list[0].Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.585,0.13,'bright gain:'+str(ch_list[0].Gain), color='whitesmoke')
        axs[1,1].set_title(ch_list[0].ChannelName+':  '+ch_list[0].Name, size=12)
        axs[1,1].set_xlabel('X $\mu$m')
        axs[1,1].set_ylabel('Y $\mu$m')
        
        im4 = axs[1, 0].imshow(CS[:,:,:,1], extent=extent)
        if ch_list[1].Gain != 1 & show_gain_on_Images==True:
           plt.figtext(0.16,0.13,'bright gain:'+str(ch_list[1].Gain), color='whitesmoke')
        axs[1,0].set_title(ch_list[1].ChannelName+':  '+ch_list[1].Name, size=12)
        axs[1,0].set_xlabel('X $\mu$m')
        axs[1,0].set_ylabel('Y $\mu$m')
        
        plt.savefig(d_name+'\\'+f_name+'_Intensity_2ch.png',dpi=300)
        plt.show()
    



    
    """################################################################
    ####   plot 3 figure color FRET image based by 2 channels         ###
    ###############################################################"""
    
    if FRET==True:
    
        print('[Image] Reference #3 FRET')
                
        Donor_APD_Channel=Read_FRET_Donor_Ch_index(ch_list)
        Acceptor_APD_Channel=Read_FRET_Acceptor_Ch_index(ch_list)
                        
        Config_Donor=ch_list[Donor_APD_Channel]
        Config_Acceptor=ch_list[Acceptor_APD_Channel]
        
        print('Donor    Ch'+str(Config_Donor.Channel+1)+': '+Config_Donor.Name)
        print('Acceptor Ch'+str(Config_Acceptor.Channel+1)+': '+Config_Acceptor.Name)
        
        Donor=CZ[Z_Slice,:,:,Donor_APD_Channel]+1
        Acceptor=CZ[Z_Slice,:,:,Acceptor_APD_Channel]+1
        Threshold=np.mean(Donor)+3*np.std(Donor)
        FRET_Ratio=Acceptor/(Acceptor+Donor)
        Mask=1*((Donor+Acceptor) >Threshold)
        
        #Construct figure
        fig, axs = plt.subplots(2, 2, figsize=(14, 12))
        rect = fig.patch  #modify background color
        rect.set_facecolor('whitesmoke')
        #fig.suptitle('- PicoQuant MT200 -', fontsize=14, weight='bold')
        plt.figtext(0.125,0.94,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.92,'Date: '+date[0]+'     '+Excitation+Objective+'    Fret-Mask '+str(int(Threshold))+' cts')
        plt.figtext(0.126,0.90, DwellTime)
        
        im1 = axs[0, 0].imshow(FRET_Ratio*Mask, cmap='jet', extent=extent)
        #im1 = axs[0, 0].imshow(Acceptor, cmap='gray', extent=extent)
        axs[0,0].set_title('FRET Efficiency', size=12)
        axs[0,0].set_xlabel('X $\mu$m')
        axs[0,0].set_ylabel('Y $\mu$m')
        cbar=fig.colorbar(im1, ax=axs[0, 0], fraction=0.065, pad=0.02)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label('FRET Efficiency', labelpad=8, rotation=90)
        
        im2 = axs[0, 1].imshow(CS[:,:,:,Donor_APD_Channel]+CS[:,:,:,Acceptor_APD_Channel], extent=extent)
        if Config_Donor.Gain * Config_Acceptor.Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.585,0.54,'Brightness:'+str(ch_list[Donor_APD_Channel].Color+str(ch_list[Donor_APD_Channel].Gain)+'x '+str(ch_list[Acceptor_APD_Channel].Color)+' '+str(ch_list[Acceptor_APD_Channel].Gain)+'x', color='whitesmoke'))
        axs[0,1].set_title(Config_Donor.Color+': '+Config_Donor.Name+' - '+Config_Acceptor.Color+': '+Config_Acceptor.Name, size=12)
        axs[0,1].set_xlabel('X $\mu$m')
        axs[0,1].set_ylabel('Y $\mu$m')
                
        im3 = axs[1, 1].imshow(CS[:,:,:,Donor_APD_Channel], extent=extent)
        if ch_list[0].Gain != 1 & show_gain_on_Images==True:
           plt.figtext(0.16,0.13,'bright gain:'+str(Config_Donor), color='whitesmoke')
        axs[1,1].set_title('Donor: '+Config_Donor.ChannelName+':  '+Config_Donor.Name, size=12)
        axs[1,1].set_xlabel('X $\mu$m')
        axs[1,1].set_ylabel('Y $\mu$m')
        
        im4 = axs[1, 0].imshow(CS[:,:,:,Acceptor_APD_Channel], extent=extent)
        if Config_Acceptor.Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.585,0.13,'bright gain:'+str(Config_Acceptor.Gain), color='whitesmoke')
        axs[1,0].set_title('Acceptor: '+Config_Acceptor.ChannelName+':  '+Config_Acceptor.Name, size=12)
        axs[1,0].set_xlabel('X $\mu$m')
        axs[1,0].set_ylabel('Y $\mu$m')
                   
        plt.savefig(d_name+'\\'+f_name+'_FRET_Efficiency_image.png',dpi=300)
        plt.show()
        
        Plot_FRET_Histogram(FRET_Ratio*Mask,80,True)       
        


    """plot 4 figure color image based by 3 channels"""
    
    if len(ch_list)==3 and ShowDefault==True:
        print('plot reference #4')
                #Construct figure
        fig, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
        rect = fig.patch  #modify background color
        rect.set_facecolor('whitesmoke')
        #fig.suptitle('- PicoQuant MT200 -', fontsize=14, weight='bold')
        plt.figtext(0.125,0.925,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.90,'Date: '+date[0]+'       '+Excitation+Objective)
        plt.figtext(0.126,0.88, DwellTime)
        
        im1 = axs[0].imshow(intensity_image, cmap='gray', extent=extent)
        axs[0].set_title('Combined intensity', size=12)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        cbar=fig.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label('Intensity counts', labelpad=8, rotation=90)
        
        im2 = axs[1].imshow(CS[:,:,:,0]+CS[:,:,:,1]+CS[:,:,:,2], extent=extent)
        if ch_list[0].Gain * ch_list[1].Gain * ch_list[2].Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.56,0.16,'Brightness:'+ch_list[0].Color+str(ch_list[0].Gain)+'x '+ch_list[1].Color+' '+str(ch_list[1].Gain)+'x '+ch_list[2].Color+' '+str(ch_list[2].Gain)+'x', color='whitesmoke')
        axs[1].set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[1].Color+': '+ch_list[1].Name+' - '+ch_list[2].Color+': '+ch_list[2].Name, size=12)
        axs[1].set_xlabel('X $\mu$m')
        axs[1].set_ylabel('Y $\mu$m')
        
        plt.savefig(d_name+'\\'+f_name+'_Intensity_3ch.png',dpi=300)
        plt.show()
    
    
    """plot 5 figure color image for 4 channels"""
    
    if len(ch_list)==4  and ShowDefault==True:
        print('plot reference #5')
        fig, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
        rect = fig.patch  #modify background color
        rect.set_facecolor('whitesmoke')
        #fig.suptitle('- PicoQuant MT200 -', fontsize=14, weight='bold')
        plt.figtext(0.125,0.925,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.90,'Date: '+date[0]+'       '+Excitation+Objective)
        plt.figtext(0.126,0.88, DwellTime)
        
        im1 = axs[0].imshow(intensity_image, cmap='gray', extent=extent)
        axs[0].set_title('Combined intensity', size=12)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        cbar=fig.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label('Intensity counts', labelpad=8, rotation=90)
        
        im2 = axs[1].imshow(CS[:,:,:,0]+CS[:,:,:,1]+CS[:,:,:,2]+CS[:,:,:,3], extent=extent)
        if ch_list[0].Gain * ch_list[1].Gain * ch_list[2].Gain * ch_list[3].Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.56,0.16,'Brightness:'+ch_list[0].Color+str(ch_list[0].Gain)+'x '+ch_list[1].Color+str(ch_list[1].Gain)+'x '+ch_list[2].Color+str(ch_list[2].Gain)+'x '+ch_list[3].Color+str(ch_list[3].Gain)+'x ', color='whitesmoke')
        axs[1].set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[1].Color+': '+ch_list[1].Name+' - '+ch_list[2].Color+': '+ch_list[2].Name+' - '+ch_list[3].Color+': '+ch_list[3].Name, size=12)
        axs[1].set_xlabel('X $\mu$m')
        axs[1].set_ylabel('Y $\mu$m')
        
        plt.savefig(d_name+'\\'+f_name+'_Intensity_4ch.png',dpi=300)
        plt.show()
    
        #save data files
    
    if Save_data_files==True:
        for i in ch_listst:
            # Datafiles are saved
            print('Saved datafile '+i)
            if i == 'Ch1':  
                np.savetxt(d_name+'\\'+f_name+'_Ch1_'+Config1.Name+'.dat', Ch1, delimiter=',',fmt='%i')
            if i == 'Ch2':
                np.savetxt(d_name+'\\'+f_name+'_Ch2_'+Config2.Name+'.dat', Ch2, delimiter=',',fmt='%i')
            if i == 'Ch3':  
                np.savetxt(d_name+'\\'+f_name+'_Ch3_'+Config3.Name+'.dat', Ch3, delimiter=',',fmt='%i')
            if i == 'Ch4':
                np.savetxt(d_name+'\\'+f_name+'_Ch4_'+Config4.Name+'.dat', Ch4, delimiter=',',fmt='%i')
        
        if  FRET==True:
            np.savetxt(d_name+'\\'+f_name+'_FRET_Efficiency.dat', FRET_Ratio, delimiter=',',fmt='%.3f')
            np.savetxt(d_name+'\\'+f_name+'_FRET_Efficiency_Mask.dat', Mask, delimiter=',',fmt='%i')
            np.savetxt(d_name+'\\'+f_name+'_FRET_Efficiency_x_Mask.dat', FRET_Ratio*Mask, delimiter=',',fmt='%.3f')
            print('Saved FRET Efficiency datafiles ')
    

    """###############################################################
    ####   Next section can be used to add user configured images  ###
    ###############################################################"""
# Plot GB vs RGB image

    if USER_1==True and len(ch_list)==3:
        print('plot reference #6 user 1')
        
        #Construct figure
        fig, axs = plt.subplots(1, 2, figsize=(15.9, 8))
        rect = fig.patch  #modify background color
        rect.set_facecolor('whitesmoke')
       # fig.suptitle('- PicoQuant MT200 -', fontsize=14, weight='bold')
        plt.figtext(0.125,0.925,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.90,'Date: '+date[0]+'      '+Excitation+Objective)
        plt.figtext(0.126,0.88, DwellTime)
        
        im1 = axs[0].imshow(CS[:,:,:,1]+CS[:,:,:,2], extent=extent)
        if ch_list[0].Gain*ch_list[1].Gain*ch_list[2].Gain != 1 & show_gain_on_Images==True:
            plt.figtext(0.14,0.16,'Brightness:'+ch_list[0].Color+str(ch_list[0].Gain)+'x '+ch_list[1].Color+' '+str(ch_list[1].Gain)+'x '+ch_list[2].Color+'x', color='whitesmoke')
        axs[0].set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[2].Color+': '+ch_list[2].Name, size=12)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        
        im2 = axs[1].imshow(CS[:,:,:,0]+CS[:,:,:,1]+CS[:,:,:,2], extent=extent)
        if ch_list[0].Gain * ch_list[1].Gain * ch_list[2].Gain  != 1 & show_gain_on_Images==True:
            plt.figtext(0.56,0.16,'Brightness:'+ch_list[0].Color+str(ch_list[0].Gain)+'x '+ch_list[1].Color+' '+str(ch_list[1].Gain)+'x '+ch_list[2].Color+' '+str(ch_list[2].Gain)+'x', color='whitesmoke')
        axs[1].set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[1].Color+': '+ch_list[1].Name+' - '+ch_list[2].Color+': '+ch_list[2].Name, size=12)
        axs[1].set_xlabel('X $\mu$m')
        axs[1].set_ylabel('Y $\mu$m')
        
        plt.savefig(d_name+'\\'+f_name+'_GB_vs_RGB.png',dpi=300)
        plt.show()


#plot 7 - Option to plt Red Intensity map vs RGB colour

    if  USER_2==True and len(ch_list)==3:
        print('plot reference #7 user 2')
        fig, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
        rect = fig.patch  #modify background color
        rect.set_facecolor('whitesmoke')
        plt.figtext(0.125,0.925,'File: '+f_name, fontsize=14, weight='medium')
        plt.figtext(0.127,0.90,'Date: '+date[0]+'       '+Excitation+Objective)
        plt.figtext(0.126,0.88, DwellTime)
        
        im1 = axs[0].imshow(Ch1, cmap='gray', extent=extent)
        axs[0].set_title('Red 20nm beads', size=12)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        cbar=fig.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02)
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label('Intensity counts', labelpad=8, rotation=90)
        
        im2 = axs[1].imshow(CS[:,:,:,0]+CS[:,:,:,1]+CS[:,:,:,2], extent=extent)
        if ch_list[0].Gain * ch_list[1].Gain * ch_list[2].Gain  != 1 & show_gain_on_Images==True:
            plt.figtext(0.56,0.16,'Brightness:'+ch_list[0].Color+str(ch_list[0].Gain)+'x '+ch_list[1].Color+' '+str(ch_list[1].Gain)+'x '+ch_list[2].Color+' '+str(ch_list[2].Gain)+'x', color='whitesmoke')
        axs[1].set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[1].Color+': '+ch_list[1].Name+' - '+ch_list[2].Color+': '+ch_list[2].Name, size=12)
        axs[1].set_xlabel('X $\mu$m')
        axs[1].set_ylabel('Y $\mu$m')
        
        plt.savefig(d_name+'\\'+f_name+'_Red_Intensity_vs_RGB.png',dpi=300)
        plt.show()   
        
       
    if Zstack==True:
        Z_Slice +=1
        
        
"""----------END Of FILES Forloop-----------------------"""

if SaveConvertedBin==True:
    #Just a option to save a .npy stack
    np.save(d_name+'\\'+f_name+'_ConvertedBin.npy',CZ)


"""##############################################
####       3D projection                      ###
##############################################"""
#This section makes 3D projections and orthogonal image planes

if Plot_OrthogonalProjections==True and Zstack==True and len(path_select)<=2:
    print('Note: OrthogonalProjection is canceled becasue you selected only one .ptu file')
    
if Plot_OrthogonalProjections==True and Zstack==True and len(path_select)>=2:
    #check if centerlines are set OK within image size
    
    print('plot 3D orthogonal image')
    
    Xr = range(1,ptu_file.head["ImgHdr_PixX"]-int(WidthX/2))
    if (Hor_centerlineY in Xr) == False:
        Hor_centerlineY=ptu_file.head["ImgHdr_PixX"]/2
        print('X centerline out of range')
    Yr = range(1,ptu_file.head["ImgHdr_PixY"]-int(WidthY/2))
    if (Vert_centerlineX in Yr)==False:
        print('Y centerline out of range')
        Vert_centerlineX=ptu_file.head["ImgHdr_PixY"]/2
    Hor_centerlineY=int(Hor_centerlineY)
    Vert_centerlineX=int(Vert_centerlineX)
    
    OrthoString= 'X'+str(Vert_centerlineX)+'/'+str(WidthX)+'p : Y'+str(Hor_centerlineY)+'/'+str(WidthY)+'p'
    
    #Make Projections from CZ based with method 'mean' or 'max'
    if projection=='max':
        CZxy=np.max(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),:,:,:], axis=0)
        if FlipZ==True:
            CZxz=np.max(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),:,(Hor_centerlineY-int(WidthY/2)):(Hor_centerlineY+int(WidthY/2))+1,:], axis=2) #RIGHT
            CZyz=np.flipud(np.max(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),Vert_centerlineX-int(WidthX/2):Vert_centerlineX+int(WidthX/2)+1,:,:], axis=1)) #TOP
        else:
            CZxz=np.flipud(np.max(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),:,(Hor_centerlineY-int(WidthY/2)):(Hor_centerlineY+int(WidthY/2))+1,:], axis=2)) #RIGHT
            CZyz=np.max(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),Vert_centerlineX-int(WidthX/2):Vert_centerlineX+int(WidthX/2)+1,:,:], axis=1) #TOP
        
    elif projection=='mean':
        CZxy=np.mean(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),:,:,:], axis=0)
        if FlipZ==True:
            CZxz=np.mean(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),:,(Hor_centerlineY-int(WidthY/2)):(Hor_centerlineY+int(WidthY/2))+1,:], axis=2) #RIGHT
            CZyz=np.flipud(np.mean(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),Vert_centerlineX-int(WidthX/2):Vert_centerlineX+int(WidthX/2)+1,:,:], axis=1)) #TOP
        else:
            CZxz=np.flipud(np.mean(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),:,(Hor_centerlineY-int(WidthY/2)):(Hor_centerlineY+int(WidthY/2))+1,:], axis=2)) #RIGHT
            CZyz=np.mean(CZ[StripZ_top:(len(Z_section)-StripZ_coverslip),Vert_centerlineX-int(WidthX/2):Vert_centerlineX+int(WidthX/2)+1,:,:], axis=1) #TOP
    #Set Orthogalimages Xz and Yz range
    extentX=[Z_section[StripZ_top],Z_section[len(Z_section)-StripZ_coverslip-1], ptu_file.head["ImgHdr_PixY"]*ptu_file.head["ImgHdr_PixResol"],0]
    extentY=[0, ptu_file.head["ImgHdr_PixX"]*ptu_file.head["ImgHdr_PixResol"],Z_section[StripZ_top],Z_section[len(Z_section)-StripZ_coverslip-1]]
    
    fig, ax_3DProject = plt.subplots(figsize=(7, 8.5))
    
    if len(ch_list)==1:
        ax_3DProject.imshow(Fill_colour(CZxy[:,:,0], ch_list[0].Color), extent=extent)
    elif len(ch_list)==2:    
        ax_3DProject.imshow(Fill_colour(CZxy[:,:,0], ch_list[0].Color)+Fill_colour(CZxy[:,:,1], ch_list[1].Color), extent=extent)
    elif len(ch_list)==3:
        ax_3DProject.imshow(Fill_colour(CZxy[:,:,0], ch_list[0].Color)+Fill_colour(CZxy[:,:,1], ch_list[1].Color)+Fill_colour(CZxy[:,:,2], ch_list[2].Color),  extent=extent)
    elif len(ch_list)==4:
        ax_3DProject.imshow(Fill_colour(CZxy[:,:,0], ch_list[0].Color)+Fill_colour(CZxy[:,:,1], ch_list[1].Color)+Fill_colour(CZxy[:,:,2], ch_list[2].Color)+Fill_colour(CZxy[:,:,3], ch_list[3].Color),  extent=extent)   
    
    plt.figtext(0.125,0.925,'File: '+f_name, fontsize=13, weight='medium')
    plt.figtext(0.127,0.90,'Date: '+date[0]+'       '+Excitation+Objective)
    plt.figtext(0.127,0.88,projection+' Z-Projection'+'        '+OrthoString+'        '+DwellTime)
    
    ax_3DProject.set_xlabel('X $\mu$m')
    ax_3DProject.set_ylabel('Y $\mu$m')
    
    if Centerline=='ON':
        plt.axvline(x=Vert_centerlineX*ptu_file.head["ImgHdr_PixResol"],color='white', alpha=0.3)
        plt.axhline(y=Hor_centerlineY*ptu_file.head["ImgHdr_PixResol"],color='white', alpha=0.3)
        
    divider = make_axes_locatable(ax_3DProject)
    ax_orthoProjX = divider.append_axes("top", 1, pad=0.25, sharex=ax_3DProject)
    ax_orthoProjY = divider.append_axes("right",1, pad=0.25, sharey=ax_3DProject)
    
    if len(ch_list)==1:
        ax_orthoProjY.imshow(Fill_colour(CZxz[:,:,0].T, ch_list[0].Color, Normed2=np.max(CZxz[:,:,0])), aspect='auto',  extent=extentX)
        ax_orthoProjX.imshow(Fill_colour(CZyz[:,:,0],   ch_list[0].Color, Normed2=np.max(CZyz[:,:,0])), aspect='auto',  extent=extentY)        
    elif len(ch_list)==2:
        ax_orthoProjY.imshow(Fill_colour(CZxz[:,:,0].T, ch_list[0].Color, Normed2=np.max(CZxz[:,:,0]))+Fill_colour(CZxz[:,:,1].T, ch_list[1].Color, Normed2=np.max(CZxz[:,:,1])), aspect='auto',  extent=extentX)
        ax_orthoProjX.imshow(Fill_colour(CZyz[:,:,0],   ch_list[0].Color, Normed2=np.max(CZyz[:,:,0]))+Fill_colour(CZyz[:,:,1],   ch_list[1].Color, Normed2=np.max(CZyz[:,:,1])), aspect='auto',  extent=extentY)        
    elif len(ch_list)==3:
        ax_orthoProjY.imshow(Fill_colour(CZxz[:,:,0].T, ch_list[0].Color, Normed2=np.max(CZxz[:,:,0]))+Fill_colour(CZxz[:,:,1].T, ch_list[1].Color, Normed2=np.max(CZxz[:,:,1]))+Fill_colour(CZxz[:,:,2].T, ch_list[2].Color, Normed2=np.max(CZxz[:,:,2])), aspect='auto',  extent=extentX)
        ax_orthoProjX.imshow(Fill_colour(CZyz[:,:,0],   ch_list[0].Color, Normed2=np.max(CZyz[:,:,0]))+Fill_colour(CZyz[:,:,1],   ch_list[1].Color, Normed2=np.max(CZyz[:,:,1]))+Fill_colour(CZyz[:,:,2],   ch_list[2].Color, Normed2=np.max(CZyz[:,:,2])), aspect='auto',  extent=extentY)
    elif len(ch_list)==4:
        ax_orthoProjY.imshow(Fill_colour(CZxz[:,:,0].T, ch_list[0].Color, Normed2=np.max(CZxz[:,:,0]))+Fill_colour(CZxz[:,:,1].T, ch_list[1].Color, Normed2=np.max(CZxz[:,:,1]))+Fill_colour(CZxz[:,:,2].T, ch_list[2].Color, Normed2=np.max(CZxz[:,:,2]))+Fill_colour(CZxz[:,:,3].T, ch_list[3].Color, Normed2=np.max(CZxz[:,:,3])), aspect='auto',  extent=extentX)
        ax_orthoProjX.imshow(Fill_colour(CZyz[:,:,0],   ch_list[0].Color, Normed2=np.max(CZyz[:,:,0]))+Fill_colour(CZyz[:,:,1],   ch_list[1].Color, Normed2=np.max(CZyz[:,:,1]))+Fill_colour(CZyz[:,:,2],   ch_list[2].Color, Normed2=np.max(CZyz[:,:,2]))+Fill_colour(CZyz[:,:,3],   ch_list[3].Color, Normed2=np.max(CZyz[:,:,3])), aspect='auto',  extent=extentY)
    
    ax_orthoProjX.set_title(ch_list[0].Color+': '+ch_list[0].Name+' - '+ch_list[1].Color+': '+ch_list[1].Name, size=12)    
    ax_orthoProjX.xaxis.set_tick_params(labelbottom=False)
    ax_orthoProjY.yaxis.set_tick_params(labelleft=False)
    ax_orthoProjX.set_yticks(np.linspace(Z_section[StripZ_top],Z_section[len(Z_section)-StripZ_coverslip-1],5))
    ax_orthoProjX.set_ylabel('xZ $\mu$m')
    ax_orthoProjY.set_xticks(np.linspace(Z_section[StripZ_top],Z_section[len(Z_section)-StripZ_coverslip-1],3))
    ax_orthoProjY.set_xlabel('yZ $\mu$m')
    
    plt.savefig(d_name+'\\'+f_name+'_3D_stack.png',dpi=300)
    plt.show()

if Plot_mean_Zplane_Intensity==True and Zstack==True and len(path_select)>=2:
    #Plot average intensity vs Z-slice
    Colour_curve=np.zeros((len(Z_section),len(ch_list)))
   
    j=0
    for i in Z_section: #loop over the z-slices
        jj=0
        for ch in ch_list: #loop over the "colors" channels
            #intensity thresholding to delete low intensities.
            if Zplane_threshold != 0:
                Threshold_Zplane_val=np.mean(CZ[j,:,:,jj])+Zplane_threshold*np.std(CZ[j,:,:,jj])   #autotreshold
                intensityDropped_Zplane=np.delete(CZ[j,:,:,jj].flatten(), np.where(CZ[j,:,:,jj].flatten() <=Threshold_Zplane_val))
                Colour_curve[j,jj]=np.mean(intensityDropped_Zplane)
            else:
                Colour_curve[j,jj]=np.mean(CZ[j,:,:,jj])    
            jj+=1
        j+=1

    if len(ch_list)==1:
        plt.plot(Z_section,Colour_curve[:,0],'r')
    if len(ch_list)==2:
        plt.plot(Z_section,Colour_curve[:,0],'r',Z_section,Colour_curve[:,1],'g')
    if len(ch_list)==3:
        plt.plot(Z_section,Colour_curve[:,0],'r',Z_section,Colour_curve[:,1],'g', Z_section,Colour_curve[:,2],'b')
    if len(ch_list)==4:
        plt.plot(Z_section,Colour_curve[:,0],'r',Z_section,Colour_curve[:,1],'g', Z_section,Colour_curve[:,2],'b', Z_section,Colour_curve[:,3],'k')
        
    plt.title('average intensity')
    plt.xlabel('Z-section  $\mu$m')
    plt.ylabel('mean intensity')

#ERROR Summary

if len(Errors) != 1  and len(path_select) >= 2:
    print('FLIM file-conversion errors in:')
    for Err in Errors:
        print(Err)
elif len(Errors) == 1 and len(path_select) >= 2:
    print('All *.PTU files proccessed succesfully')     



