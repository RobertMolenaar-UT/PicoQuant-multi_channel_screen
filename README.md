# PicoQuant-multi channel screen
Batch proccessing, that converts PiqoQuant PTU into fluorescent image

This script can generate multicolour images in an automized way.
The PTU conversion is done by

https://github.com/RobertMolenaar-UT/readPTU_FLIM

Main purpose of the script is one can proccess a batch or folder of PTU files and get a series fluorescent multicolor images with minimal user input.
install wx python for file selector app.


Each file is checked for
- it is a 2D  image
- Used channels channels
- 'PIE'  or 'normal' excitation.

You need to define the channels in the initial part of the code:
                  Ch,         NameLabel,        Coloring,   Gain,   PIE TimeGate, FRET
Config1 = Set_Channel_Info(1,   'Alexa647'      ,   'Red'      ,2      ,1 ,      'donor')
Config2 = Set_Channel_Info(2,   'Alexa488'      ,   'Green'    ,2      ,2 ,      'acceptor')
Config3 = Set_Channel_Info(3,   'DAPI-1         ,   'Blue'     ,2      ,3 ,       '-')
Config4 = Set_Channel_Info(4,   'DAPI-2'        ,   'Blue'     ,2      ,3 ,       '-')

Each channel is normalized from 0:1 and added into a RGB color image.
Availabe colors: 'Red', 'Green', 'YGreen' , 'Blue', 'Magenta', 'Cyan', 'Orange','Yellow'
Picoquant PIE TimeGates LASER fireing order is from the longst wavelenght to the shortest.
Optional FRET set 'donor', and 'acceptor'










