# Importing a context from one node into another

To import a context from a node that currently hosts contextIds linked under that context into another node:

#### 1) Set one time passcode

The admin of the node that currently hosts context should use [brightid cli](https://github.com/BrightID/brightid-cli#set-passcode) to set a one time passcode on the context to authorize the new node request for getting context info, and share this passcode with the admin of the new node.

```
$ sudo pip3 install brightidcli
$ brightid admin set-passcode --context <context> --passcode <passcode>
Done
```

#### 2) Stop the `consensus_receiver`

To ensure that the new node will not miss contextIds that are linked while importing the context, its admin should stop the `consensus_receiver` service before importing.

```
$ cd BrightID-Node-docker
$ docker-compose stop consensus_receiver
Stopping brightid-node_consensus_receiver_1 ... done
```

#### 3) Import the context
The admin of the new node should use [brightid cli](https://github.com/BrightID/brightid-cli#import-context) to import the context into the node.

```
$ sudo pip3 install brightidcli
$ brightid admin import-context --context <context> --remote-node <remote-node-address> --passcode <passcode>
Checking if the consensus receiver is stopped ...
Getting data ...
Importing context ...
Done
```

#### 4) Restart the node
The node should be restarted after importing the context to start `consensus_receiver` again and also enable `ws` service load the new imported collections.

```
$ cd BrightID-Node-docker
$ docker-compose restart
Restarting brightid-node_consensus_receiver_1 ... done
Restarting brightid-node_consensus_sender_1   ... done
Restarting brightid-node_scorer_1             ... done
Restarting brightid-node_ws_1                 ... done
Restarting brightid-node_updater_1            ... done
Restarting brightid-node_db_1                 ... done
Restarting brightid-node_web_1                ... done
```
