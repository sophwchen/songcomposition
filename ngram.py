"""
This file includes functions to:
    - train an n-gram model
    - generate a melodic sequence
    - play a melodic sequence

To generate music using ngram:
1. history = train(samples, 5) #5 is length of n-gram
2. generatedseq = generate_music(history, 5)
"""

import numpy as np
from collections import Counter, defaultdict
from transcribe import get_notes,get_trainable_data
from note import *
import os

def unzip(pairs):
    return tuple(zip(*pairs))

def normalize(counter):
    total = sum(counter.values())
    return [(char, cnt / total) for char, cnt in counter.most_common()]

def train(samples, n):
    raw_lm = defaultdict(Counter)
    for sample in samples:
        history = ["~" for i in range(n-1)]
        history = tuple(history)
        for note in sample:
            history = tuple(history)
            raw_lm[history][note] += 1
            history = list(history[1:])
            history.append(note)
    lm = {history: normalize(counter) for history, counter in raw_lm.items()}
    return lm

def generate_note(lm, history):
    if not history in lm:
        return history[np.random.choice(len(history))]
    notes, probs = unzip(lm[history])
    i = np.random.choice(np.arange(len(notes)), p=probs)
    return notes[i]

def generate_music(start_note,lm, n, num_notes=100,*,upper_bound=72,lower_bound = 24):
    start_n = note_to_n(start_note[0],start_note[1])
    history = ["~" for i in range(n-1)]
    phrase = []
    prev_note = start_n
    for i in range(num_notes):
        history = tuple(history)
        c = generate_note(lm, history)
        if c[0]+prev_note>upper_bound or c[0]+prev_note<lower_bound:
            c = (0,c[1])
        phrase.append((c[0]+prev_note,c[1]))
        history = list(history[1:])
        history.append(c)
        prev_note += c[0]
    return phrase

def note_to_samples(notes,tempo,sampling_rate=44100):
    samples = np.array([])
    current_time=0
    for note in notes:
        note_n = note[0]
        note_freq = round(440 * (2**((note_n-58)/12)),2)
        note_length = note[1]
        note_times = np.arange(sampling_rate*current_time, sampling_rate*((note_length*60)/tempo+current_time))/sampling_rate
        note_samples = np.cos(2 * np.pi * note_freq * note_times)
        samples = np.append(samples,note_samples)
    return samples
def generate_training_data(directory):
    training_data = []
    for filename in os.listdir(directory):
        if filename[-4:] == ".mp3":
            music_path = directory+"/"+filename
            notes = get_notes(music_path,None)
            training_data.append(get_trainable_data(notes))
    return training_data
