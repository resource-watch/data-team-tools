# Hyper-V Virtual Machine Errors and Helpful Tips

## Error:
Your virtual machine, created through Hyper-V, has run out of space. 

### Solution:
Follow Step 1 in this tutorial: https://www.itworld.com/article/2833066/how-to-extend-a-linux-virtual-machine-partition-in-hyper-v.html

This will increase the space in the disk, but you need to increase the space in the file system too. Don’t follow the tutorial for this. You can easily do it using following commands:
sudo apt install gparted
sudo gparted

The partition editor will open up after that which looks like this:

You will see the size you increased in Step 1 as unallocated as your file system can’t use it yet. Right click the correct partition which might be “/dev/sda1” in this case and the following window will open up.  

You can drag the slider all the way to the right to use all the unallocated space. 

After that you can see that the size of the correct partition (/dev/sda1) has increased and unallocated space has reduced to almost zero.
