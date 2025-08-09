# Game: Enrolment Rush! A client-server course enrolment game.
## Authors: Kazi Boni Amin, Cem Sezer, Colin Sun, Jason Zhou
## CMPT 371 Summer 2025 - Group 9 

This project has no external dependencies.
Requires Python >=3.9,<3.10

Preamble: This game is meant to be run where the client and server are on separate machines. For the video demo,
the server was run on a separate machine with IPv4 address 165.227.45.38 and each client was run on
our personal machine. However, one can run the server and all the clients on one machine by using the 
loopback network for the server's address.

To change server IP address, change line 23 in client.py in the ClientConnection class.

        server_host='165.227.45.38',

Instructions: 

1. After cloning the repo, organize the files as follows:

    On one machine, the Server, should contain:
        
        socket_server.py and utils.py 
    
    Four machines, each a Client, should contain:

        main.py, utils.py, gui.py, client.py

2. Run the server using ```$python3 socket_server.py```

3. Run each client using ```$python3 main.py```

When the game starts, click start and enter your username. You will be brought to a waiting screen.
Once the game is over, the server disconnects, and can be stopped with ```ctrl+c```. 
The clients can simply be closed using quit or X button. 
# enrolmentrush
