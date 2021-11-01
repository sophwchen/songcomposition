from note import *
from scipy.stats import trim_mean,mode
from collections import Counter
import numpy as np
import librosa
from IPython.display import Audio
import matplotlib.mlab as mlab


"""cd ..
steps:
1. convert mp3 file to samples √
2. pass samples through spectrogram √
3. find peak freqs and timestamps 
4. create note objects
5. calculate semi-tone intervals between objects
6. create list of (interval, length) or (note name, length)
7. ???
8. profit
"""

def mp3_path_to_samples(path: str,*,duration = None, sampling_rate=44100) -> np.array:
    samples, sampling_rate = librosa.load(path, sr=sampling_rate, mono=True, duration=duration)
    onset_env = librosa.onset.onset_strength(samples, sr=sampling_rate)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sampling_rate)
    return np.array(samples), round(tempo[0])

def get_peaks(spectrum, freqs,high_cutoff,low_cutoff,cluster_spread:int,cluster_max:int,bleed:int):
    highest_freqs = []
    new_note_idxs = [i for i in range(spectrum.shape[1]) if trim_mean(spectrum[:,i],0.1) > high_cutoff]
    note_starts = []
    note_ends = []
    cluster_idxs = []
    cluster_means = []
    prev = new_note_idxs[0]
    prev_freq = freqs[np.argmax(spectrum[:,prev])]
    for i in range(len(new_note_idxs)):
        idx = new_note_idxs[i]
        current_freq  = freqs[np.argmax(spectrum[:,idx])]
        if idx-prev <= cluster_spread and len(cluster_means)<cluster_max:
            cluster_idxs.append(idx)
            cluster_means.append(trim_mean(spectrum[:,idx],0.1))
        else:
            column_idx = cluster_idxs[np.argmax(cluster_means)]
            note_starts.append(column_idx)
            if column_idx+bleed<spectrum.shape[1]-1:
                highest_freq_idx = np.argmax(spectrum[:,column_idx+bleed])
                highest_freq_idxs = spectrum[:,column_idx+bleed].argsort()[-2:][::-1]
                score1 = spectrum[highest_freq_idxs[0],column_idx+bleed]
                score2 = spectrum[highest_freq_idxs[1],column_idx+bleed]
            else:
                highest_freq_idx = np.argmax(spectrum[:,-1])
                highest_freq_idxs = spectrum[:,-1].argsort()[-2:][::-1]
                score1 = spectrum[highest_freq_idxs[0],column_idx]
                score2 = spectrum[highest_freq_idxs[1],column_idx]
            freq1 = freqs[highest_freq_idxs[0]]
            freq2 = freqs[highest_freq_idxs[1]]
            if (score2*1.2>score1 and freq2<freq1) or octave_lower(freq1,freq2):
                    highest_freq_idx = highest_freq_idxs[1]
            highest_freqs.append(freqs[highest_freq_idx])
            cluster_idxs = [idx]
            cluster_means = [trim_mean(spectrum[:,idx],0.1)]
        prev = idx
        prev_freq = current_freq
    column_idx = cluster_idxs[np.argmax(cluster_means)]
    note_starts.append(column_idx)        
    if column_idx+bleed<spectrum.shape[1]-1:
        highest_freq_idx = np.argmax(spectrum[:,column_idx+bleed])
    else:
        highest_freq_idx = np.argmax(spectrum[:,-1])
    highest_freqs.append(freqs[highest_freq_idx])
    
    separations = note_starts
    separations.append(spectrum.shape[1]-1)
    for i in range(len(separations)-1):
        note_start = separations[i]
        next_note_start = separations[i+1]
        found_col = False
        for i in range(note_start,next_note_start):
            col = spectrum[:,i]
            if np.mean(col) < low_cutoff:
                found_col = True
                note_ends.append(i)
                break
        if not found_col:
            note_ends.append(next_note_start)
    return highest_freqs,np.array(note_starts[:-1]),np.array(note_ends) 
def round_to_note_lengths(lengths):
    note_lengths = np.array([1/16,1/8,3/16,1/4,3/8,1/3,1/2,3/4,1,3/2])
    out_lengths = []
    for length in lengths:
        idx = np.abs(note_lengths-length).argmin()
        out_lengths.append(note_lengths[idx])
    return out_lengths
def standardize_lengths(starts,ends,times,tempo,tolerance): 
    note_lengths_idxs = ends-starts
    length_counter = Counter()
    for length in note_lengths_idxs:
        length_counter[length] +=1
    keys = sorted(length_counter.keys())
    lengths = []
    clusters = []
    cluster = []
    prev = keys[0]
    for key in keys:
        if abs(key-prev) < tolerance:
            for i in range(length_counter[key]):
                cluster.append(key)
        else:
            cluster = np.array(cluster)
            _mode = mode(cluster)[0][0]
            lengths.append(_mode)
            clusters.append(cluster)
            cluster = [key]
        prev = key
    cluster = np.array(cluster)
    _mode = mode(cluster)[0][0]
    lengths.append(_mode)
    lengths = np.array(lengths,dtype=np.int64)
    clusters.append(cluster)
    note_lengths_times = times[lengths] - times[0]
    note_lengths_times = np.round(note_lengths_times,2)
    
    beats = (note_lengths_times/60)*tempo
    beats = round_to_note_lengths(beats)
    out_dict = {}
    for i in range(len(beats)):
        for item in clusters[i]: 
            if item not in out_dict:
                out_dict[item]=beats[i]
    return out_dict
def notes_from_peaks(freqs,times,note_starts,note_ends,tempo):
    count=0
    out = []
    increase=0
    idxs2beats = standardize_lengths(note_starts,note_ends,times,tempo,2)
    for i in range(len(note_starts)):
        freq = freqs[i]
        note_start = note_starts[i]
        note_end = note_ends[i]
        length = note_end-note_start
        if freq>0 and (length > 5 or len(out)==0):
            beats = idxs2beats[length]
            out.append(Note(freq,beats))
        """
        if(i+1<len(note_starts)):
            rest_length = note_starts[i+1]-note_ends[i]
            if rest_length>5:
                beats = rest_length
                out.append(Note(0,))
        """
    return out
def notes_to_samples(notes,times,note_starts,note_ends,tempo,sampling_rate=44100):
    samples = np.array([])
    note_times = np.array([])
    current_time = 0
    separations = list(note_starts)
    separations.append(len(times)-1)
    for i in range(len(notes)):
        note = notes[i]
        sample_times = np.arange(sampling_rate*current_time, sampling_rate*((note.length*60)/tempo+current_time))/sampling_rate
        sample_buffer = np.arange(sampling_rate*times[note_ends[i]],sampling_rate*times[separations[i+1]])/sampling_rate
        sample_freqs = np.cos(2 * np.pi * note.freq * sample_times)
        samples = np.append(samples,sample_freqs)
        samples = np.append(samples,np.zeros(len(sample_buffer)))
        note_times = np.append(times,sample_times)
        
    return samples,note_times
def get_notes(path,duration=None):
    samples,tempo = mp3_path_to_samples(path,duration=duration)
    spectrum, freqs, times = mlab.specgram(samples, NFFT=4096,  Fs=44100,window=mlab.window_hanning,noverlap=3240, mode='magnitude')
    high_cutoff = np.percentile(spectrum,84)
    low_cutoff = np.percentile(spectrum,90)
    peaks, starts, ends = get_peaks(spectrum,freqs,high_cutoff,low_cutoff,1,20,5)
    notes = notes_from_peaks(peaks,times,starts,ends,tempo)
    return notes

def get_trainable_data(notes):
    prev = notes[0]
    notes = []
    for i in range(len(notes)):
        note=notes[i]
        notes.append(note-prev,note.length)
        prev = note
    return notes