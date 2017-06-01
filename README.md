Right now just a Python script which forces wifi to disassociate when a more powerful AP is around.

I guess NetworkManager works just fine with disassociating and connecting another AP. But you might want to change the scan period or the specific thresholds to disconnect from the AP wifi interface is connected to.

I'll write a better README later. Also I hope to add a script with some nmcli commands to enforce proper connection too.
