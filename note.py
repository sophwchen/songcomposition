import numpy as np
import math

def note_to_n(name, octave):
    noteName = name[0]
    if noteName == "C":
        n=0
    elif noteName == "D":
        n=2 
    elif noteName == "E":
        n=4
    elif noteName == "F":
        n=6
    elif noteName == "G":
        n=8
    elif noteName == "A":
        n=10
    else:
        n=12
    if len(name) > 1:
        noteSign = name[1]
        if noteSign == "#":
            n+1
        else:
            n-1
    n+=12*octave
    return n

def n_to_note(n):
    octave = math.floor(n / 12)
    if n % 12==0:
        name = "C"
    elif n%12==1:
        name = "C#/Db"
    elif n%12==2:
        name = "D"
    elif n%12==3:
        name = "D#/Eb"
    elif n%12==4:
        name = "E"
    elif n%12==5:
        name = "F"
    elif n%12==6:
        name = "F#/Gb"
    elif n%12==7:
        name = "G"
    elif n%12==8:
        name = "G#/Ab"
    elif n%12==9:
        name = "A"
    elif n%12==10:
        name = "A#/Bb"
    else:
        name = "B"
    return name, octave

def same_note(freq1,freq2):
    return round(np.log2(freq1 / 440) * 12) + 58 == round(np.log2(freq2 / 440) * 12) + 58

def octave_lower(freq1,freq2):
    n1 = round(np.log2(freq1 / 440) * 12) + 58
    n2 = round(np.log2(freq2 / 440) * 12) + 58
    return n1-n2==12
    
class Note:
    def __init__(self, freq: float, length: float, *, style: str = None):
        """Initializes all attributes of a note
        
        Parameters
        ----------
        freq: float
            frequency of note being
        
        length: float
            length (in beats) of note

        style: str
            style of note (e.g. staccato, legato, etc.)
        """
        if(freq!=0):
            n = round(np.log2(freq / 440) * 12) + 58
            self.n = n
            self.freq = round(440 * (2**((self.n-58)/12)),2)
            self.name, self.octave = n_to_note(self.n)
        else:
            self.freq=0
            self.name="~"
            self.octave=""
        self.length = length
        self.style = None
    
    
    @property
    def attributes(self):
        """ A convenience function for getting all the attributes of a note.
        
        This can be accessed as an attribute, via `note.attributes` 
        
        Returns
        -------
        Tuple[float, float, str]
            A tuple containing all of the attributes of a note
        """
        return self.freq, self.length, self.style
    
    def __str__(self):
        return self.name + str(self.octave) + " " + str(self.length)

    def __add__(self, other):
        if isinstance(other, int):
            return self.n+other
        return self.n+other.n
    
    def __radd__(self, other):
        if isinstance(other, int):
            self.n+other
        return self.n+other.n
    
    def __sub__(self,other):
        if isinstance(other, int):
            self.n-other
        return self.n-other.n