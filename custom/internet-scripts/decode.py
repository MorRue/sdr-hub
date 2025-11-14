# taken from: https://gist.github.com/smokedsalmonbagel/271c52fa5edca07e8976fa73d37853ab
# NEITHER TESTED NOR REVIEWED

import scipy.signal
import numpy as np
import sox
import astropy.nddata
import os

# decode a .bin file to mp3.  Use with bin files from https://github.com/shajen/rtl-sdr-scanner-cpp

def convert_uint8_to_complex(data):
    sample_size = data.shape[1]
    data = (data.reshape(-1, 2).astype(np.float32) - 127.5) / 127.5
    a = data[:, 0]
    b = data[:, 1]
    return (a + b * 1j).reshape(-1, sample_size // 2)


def make_spectrogram(data, sample_rate):
    scale = 2
    fft = 2**11
    out = np.zeros(shape=(data.size // fft // scale // 2, fft // scale), dtype=np.int8)
    window = np.concatenate((np.hanning(fft // 2), np.zeros(fft // 2))).astype(np.float32)
    window = np.repeat([window], scale, axis=0).astype(np.float32)
    block_size = 2 * fft * scale
    for i in range(data.size // block_size):
        tmp = data[i * block_size : (i + 1) * block_size].astype(np.float32)
        tmp = ((tmp - 127.5) / 127.5).reshape(-1, 2)
        tmp = (tmp[:, 0] + tmp[:, 1] * 1j).reshape(-1, fft)
        tmp = np.fft.fft(tmp * window).astype(np.complex64)
        tmp = np.absolute(tmp**2.0) / np.float32(sample_rate)
        tmp = np.fft.fftshift(10.0 * np.log10(tmp), axes=(1,))
        tmp = astropy.nddata.block_reduce(tmp, scale, func=np.mean)
        out[i] = tmp.astype(np.int8)
    return out

def convert_uint8_to_float32(data):
    return (data.astype(np.float32) - 127.5) / 127.5

def shift(data, sample_rate, frequency):
    t = np.tile(np.arange(data.shape[1]), (data.shape[0], 1)) / sample_rate
    return data * np.exp(2j * np.pi * frequency * t)

def decode_fm_data(data, sample_rate, data_decimate_factor=1):
    if 1 < data_decimate_factor:
        data = scipy.signal.decimate(data, data_decimate_factor, n=1, ftype="fir")
        sample_rate = sample_rate // data_decimate_factor
    data = np.diff(np.unwrap(np.angle(data)))
    return (data, sample_rate)


def decode_am_data(data, sample_rate, data_decimate_factor=1):
    if 1 < data_decimate_factor:
        data = scipy.signal.decimate(data, data_decimate_factor, n=1, ftype="fir")
        sample_rate = sample_rate // data_decimate_factor
    data = np.abs(data)
    return (data, sample_rate)


def get_strongest_frequency(data, sample_rate):
    spectrogram = make_spectrogram(data, sample_rate)
    powers = np.mean(spectrogram, axis=0)
    max_index = np.argmax(powers)
    return int((max_index - powers.size // 2) / (powers.size // 2) * (sample_rate // 2))

def normalize(data):
    data -= data.min()
    data = data * (255.0 / data.max())
    data = data.astype(np.uint8)
    return data


def filter_human_voice(data):
    B, A = scipy.signal.butter(8, (0.025, 0.35), output="ba", btype="bandpass")
    data = scipy.signal.filtfilt(B, A, data)
    # bz, az = scipy.signal.bilinear(1, [75e-6, 1], fs=sample_rate)
    # data = scipy.signal.lfilter(bz, az, data)
    return data


def normalize_volume(data, skip_samples):
    _data = data[skip_samples:-skip_samples]
    data -= _data.mean()
    data *= 0.9 / np.max(np.abs(_data))
    return data


def decode_data(data, decoder_function, filename, sample_rate):
    diff_frequency = get_strongest_frequency(data.reshape(-1), sample_rate)
    data = convert_uint8_to_complex(data)
    data = shift(data, sample_rate, diff_frequency).reshape(-1)
    (data, sample_rate) = decoder_function(data, sample_rate, 1)
    data = filter_human_voice(data)
    data = normalize_volume(data, sample_rate // 5)
    tfm = sox.Transformer()
    tfm.set_input_format(file_type="raw", rate=sample_rate, bits=64, channels=1, encoding="floating-point")
    tfm.build_file(input_array=data, sample_rate_in=sample_rate, output_filepath=filename)

def decode(data, modulation, filename, sample_rate):
    if modulation == "FM":
        decode_data(data, decode_fm_data, filename, sample_rate)
    elif modulation == "AM":
        decode_data(data, decode_am_data, filename, sample_rate)

def convert_bin_to_mp3(bin_file_path, modulation, output_filename, sample_rate,sample_size):
    bin_bytes = os.path.getsize(bin_file_path)
    """
    Converts a binary file containing raw I/Q data to an MP3 audio file.
    Some of these args come from the sqlite3 database.  You need to
    Args:
        bin_file_path (str): Path to the binary file.
        modulation (str): Modulation type ("AM" or "FM").
        output_filename (str): Name of the output MP3 file.
        sample_rate (int): Sample rate of the data.
    """
    try:
        data = np.memmap(bin_file_path, dtype=np.uint8, mode="r")
    except Exception as e:
        print(f"Error reading binary file: {e}")
        return  # Handle the error appropriately

    factor = sample_size
    decode(data[: factor * (bin_bytes // factor)].reshape(-1, factor), modulation, output_filename, sample_rate)
    #decode(data, modulation, output_filename, sample_rate)

#example call
#                        file path of bin          Mode   out file   upper freq - lower freq    sample size (in sqlite tansmission)
# convert_bin_to_mp3('13_48_09_47340000_uint8.bin', 'FM', 'test.mp3', 47348000-47332000,         2048)
