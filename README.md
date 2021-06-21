# PicoQuant-multi channel screen
Batch proccessing, that converts PiqoQuant PTU into fluorescent image

This script can generate multicolour images in an automized way.
The PTU conversion is done by

https://github.com/RobertMolenaar-UT/readPTU_FLIM
install wx python for file selector app.

Main purpose of the script is one can proccess a batch or folder of PTU files and get a series fluorescent multicolor images with minimal user input.
Tested system : Picoquant MT200 with FLIMBEE with 4x SPAD and a multiharp 150.


Each PTU file is checked for
- if it is a 2D  image.
- Autodetect # APD channels 
- Suports 'PIE'  or 'normal' excitation
- Features Zstack image projection and FRET efficiency
- Common errors are catched and listed in the end.

You need to define the channels in the initial part of the code:
                  Ch,         NameLabel,        Coloring,   Gain,  PIE TimeGate, FRET
- Config1 = Set_Channel_Info(1, 'Alexa647'  	,   'Red'      ,2        ,1 ,      'donor')
- Config2 = Set_Channel_Info(2, 'Alexa488'    ,   'Green'    ,2        ,2 ,      'acceptor')
- Config3 = Set_Channel_Info(3,   'DAPI-1     ,   'Blue'     ,2        ,3 ,       '-')
- Config4 = Set_Channel_Info(4,   'DAPI-2'    ,   'Blue'     ,2        ,3 ,       '-')

1.  Each channel is normalized from 0:1 and added into a RGB color image.
2.  Availabe colors: 'Red', 'Green', 'YGreen' , 'Blue', 'Magenta', 'Cyan', 'Orange','Yellow'
3.  Picoquant PIE TimeGates LASER fireing order is from the longst wavelenght to the shortest. 
4.  Optionan assign FRET 'donor', and 'acceptor' channels Set *FRET =TRUE*
5.  Zstack image projection can be made of the selected Z stack files. *Zstack=True* and *Plot_OrthogonalProjections=True*



SETUP configurations.

1.  Change laser lines here in order of SEPIAII rackposition *SEPIA_laser_lines=[638,560,488,405]
2.  Set Full objective in Symphotimetime64 or in the function *Read_objective()
3.  PIE TAC ranges are auomatically calculated


Know limitiation: For bi-directional scanning, the readPTU_flim needs to be modified. 









