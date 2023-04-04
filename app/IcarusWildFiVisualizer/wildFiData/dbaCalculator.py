"""Module calculating Dynamic Body Acceleration (DBA) from a burst of acceleration data."""

import numpy as np



def calcVeDBA(dba):
    """Calculate Vector Dynamic Body Acceleration (VeDBA) from a burst of dba data (numpy array)."""
    return np.linalg.norm(dba,axis=1)

def calcODBA(dba):
    """Calculate Overall Dynamic Body Acceleration (ODBA) from a burst of dba data (numpy array)."""
    return np.sum(np.abs(dba),axis=1)

def calcDBA(accBurst):
    """Calculate Dynamic Body Acceleration (DBA) from a burst of acceleration data ((N,3) numpy array)."""
    # Calculate mean of all samples of every acceleration direction and subtract from each sample
    return accBurst - np.mean(accBurst, axis=0)