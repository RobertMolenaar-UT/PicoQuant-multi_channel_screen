# PicoQuant-multi channel screen
Batch proccessing, that converts PiqoQuant PTU into fluorescent image

This script can generate multicolour images in an automized way.
The PTU conversion is done by

https://github.com/RobertMolenaar-UT/readPTU_FLIM

Install wx python 4.0.4 for the file selector app.
Developed and tested on Python 3.7.9
Script is deleoped with a Picoquant MT200 with FLIMBEE with 4x SPAD and a multiharp 150.

the main purpose of the MultiChannel script is that one can proccess a multiple PTU files or folder with PTU files and get a series Fluorescent multicolor images with minimal user input.

Each single PTU file analysed on:  
- if it is a 2D  image.
- Autodetects the number of APD channels. 
- Supports 'PIE' and 'normal' excitation.
- Features Zstack image projection and FRET efficiency.
- Common exp file-errors are catched and reported in the end.
- Output images are stored in a seperate folder.

You do need to define the channels in the initial part of the code:

                  -                      Ch,   NameLabel,   Coloring,    Gain,  PIE TimeGate,  FRET
		  
		  Config1 = Set_Channel_Info(1, 'Alexa647'    ,   'Red'      ,2        ,1 ,      'donor')
		  Config2 = Set_Channel_Info(2, 'Alexa488'    ,   'Green'    ,2        ,2 ,      'acceptor')
		  Config3 = Set_Channel_Info(3,   'DAPI-1     ,   'Blue'     ,2        ,3 ,       '-')
		  Config4 = Set_Channel_Info(4,   'DAPI-2'    ,   'Blue'     ,2        ,3 ,       '-')
		  

1. *Namelabel*: name of the used colouring or dye.
2. *Coloring*: 	available colors are 'Red', 'Green', 'YGreen' , 'Blue', 'Magenta', 'Cyan', 'Orange','Yellow'
3. *Gain*: 	each channel is normalized from [0:1] to the max brightness in the image, use gain value to increase the brightness
4. *PIE TimeGate*: Contrast can be enhanced by using PIE excitation in the experiment to supress any cross-excitation 
	- NOTE: LASER fire order is first the longest wavelenght down to shortest wavelenght as last.
5. if applicable assign FRET 'donor', and 'acceptor' channels and enable *FRET =True*

6. Zstack image projection can be made of the selected Z stack files. Set *Zstack=True* and *Plot_OrthogonalProjections=True*
7. Save Image Intensity [count] as comma separated file *.dat*  Set Save data files = True
8. PIE TAC ranges are automatically calculated from the *.PTU* header data.

Your MT200 SETUP:

1.  Change laser lines here in order of the SEPIAII rackposition *SEPIA_laser_lines=[638,560,488,405] rack position [2,3,4,5]
2.  Set objective name in Symphotimetime64 or in the function *Read_objective()

Usage: 

Set the Configuration files according optical setup.
Run the PiqoQuant-multi_channel_screen.py.
Note the pop-up window in the taskbar and browse and select the PTU files.
Images are shown in the command line
images and data are saved in folder /Python_converted_* Username* /
Errors on files are listed in the end, in many cases these are Single Point or cancelled 2D measurements.

Known limitation: For bi-directional scanning, the readPTU_flim needs to be modified, code upon request.






-----------------------------------


# Workflow summary
 
wx 'GUI_select_Multi_file' app prompts to select (multiple) data files. 

The main For-loop proccesses all files sequentially.

1. The PTU file is read by "ptu_file  = PTUreader((path), print_header_data = False)"
2. File is checked if it's a 2D image file:
3. The PTU file is converted "flim_data_stack, intensity_image = ptu_file.get_flim_data_stack()"
4. FLIM stack is checked for avaialbe channels 'ch_list, ch_listst=Channels_list(flim_data_stack)'
5. first a CS (ColorStack) is created and [ch,x,y,RGB] 
6. second a CZ (Channel_Z) is created (Z slices, x,y,ch]
7A. Filling CZ and CS based on PIE excitation out of the flim_data_stack
	- Calculate the TimeGates
	- CZ Extract from flim_dat_stack the corresponding Ch and PIE-timeGate the stack
	- CS Extract from flim_dat_stack the corresponding Ch and PIE-timeGate the stack, and convert to colour plane by Fill_Colour()
7B. Filling CZ and CS based on Normal excitation out of the flim_data_stack
	- CZ Extract from flim_dat_stack the corresponding Ch and full TAC range the stack
	- CS Extract from flim_dat_stack the corresponding Ch and full TAC range the stack, and convert to colour plane by Fill_Colour(). 

8. Data files are saved
9. Images are created according the number of avaialble channels
10. Optional FRET 
	- FRET donor TimeGate and channels are regognized.
	- FRET efficiency is calculated per pixel.
	- Images are made. caption information is extracted from the 'configX' avaialble from the 'ch_list'
	- Mask intensity for FRET efficiency and histogram.
11. Z stack image projection and Orthogonal planes are made.
	- CZ contains [z, x,y,ch] 
	- For the XY plane the 'mean'or 'max' value is used for the x,y pixel value for each color channel.



