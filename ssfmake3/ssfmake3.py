# =====================================================================================================
# Extremely basic ssf combiner script (ver 0.14 2008-10-12) by kingshriek
# Converted to Python 3 and added command-line interface
# =====================================================================================================

from __future__ import absolute_import
from __future__ import print_function

# Default PARAMETERS
bank      = 0x00    # sequence bank number
track     = 0x00    # sequence track number
volume    = 0x7F    # volume (reduce if clipping)
mixerbank = bank    # mixer bank number (usually same as sequence bank number)
mixern    = 0x00    # mixer number (usually 0)
effect    = 0x00    # effect number (usually 0)
use_dsp   = 1       # 1: use DSP, 0: do not use DSP
# -----------------------------------------------------------------------------------------------------
# filenames - use an empty string if file isn't needed
ndrv = ''    # sound driver
nmap = ''    # sound area map
nbin = ''    # tone data
nseq = ''    # sequence data
nexb = ''    # DSP program 
# -----------------------------------------------------------------------------------------------------
nout = 'ssfdata.ssf'    # output file name (if .ssflib, create ssflib and minissfs for each track in the bank)
# =====================================================================================================

from struct import *    # pack, unpack
from array import *    # array
import os    # system, path
import argparse

# =====================================================================================================
# Converts list of bytes into a sound command list (zero-padded out to 16 bytes)
def sndcmd(x):
    if len(x) > 0x10:
        x = x[:0x10]
    return array('B', x + [0x00] * (0x10 - len(x)))
# =====================================================================================================

# =====================================================================================================
# Get base file name with and without extension
def fnoext(fname):
    fnameb = os.path.basename(fname)
    idot = -fname[::-1].find('.') - 1
    if idot:
        fnamex = fnameb[:idot]
    else:
        fnamex = fnameb
    return (fnameb, fnamex)
# =====================================================================================================

# =====================================================================================================
# Creates ssf file from user-specified parameters.
# Inputs are defined in paramter section above.
def ssfmake(nout, ndrv, nmap, nbin, nseq, nexb, bank, track, volume, mixerbank, mixern, effect, use_dsp):
    # Initialization
    szdrv = 0
    szmap = 0
    szbin = 0
    szseq = 0
    szexb = 0
    datadrv = array('B', [])
    datamap = array('B', [])
    databin = array('B', [])
    dataseq = array('B', [])
    dataexb = array('B', [])
    aseq = None
    ntracks = 0
# -----------------------------------------------------------------------------------------------------
    if ndrv != '':
        with open(ndrv, 'rb') as fdrv:    # sound driver
            szdrv = os.path.getsize(ndrv)
            datadrv = array('B', fdrv.read(szdrv))
    if nmap != '':
        with open(nmap, 'rb') as fmap:    # sound area map
            szmap = os.path.getsize(nmap)
            datamap = array('B', fmap.read(szmap))
    if nbin != '':
        with open(nbin, 'rb') as fbin:    # tone data
            szbin = os.path.getsize(nbin)
            databin = array('B', fbin.read(szbin))
    if nseq != '':
        with open(nseq, 'rb') as fseq:    # sequence data
            szseq = os.path.getsize(nseq)
            dataseq = array('B', fseq.read(szseq))
    if nexb != '':
        with open(nexb, 'rb') as fexb:    # DSP program
            szexb = os.path.getsize(nexb)
            dataexb = array('B', fexb.read(szexb))
# -----------------------------------------------------------------------------------------------------
    # Only enable DSP if a DSP file was specified
    if nexb == '' or szexb == 0:
        use_dsp = 0

    ssfbin = array('B', b'\x00' * 0x80000)
# -----------------------------------------------------------------------------------------------------
    # Set driver
    ssfbin[:szdrv] = datadrv
# -----------------------------------------------------------------------------------------------------
    # Set area map
    ssfbin[0x500:0x500 + szmap] = datamap
    offset = 0x504
    # Set transfer complete bits
    while offset < 0x600:
        ssfbin[offset] = 0x80
        offset += 0x8
# -----------------------------------------------------------------------------------------------------
    # Set sound commands
    ssoffset = 0x770    # SEQUENCE_START offset (for minissf)
    ssfbin[0x700:0x710] = sndcmd([0x87, 0x00, mixerbank, mixern])        # MIXER_CHANGE
    if use_dsp:
        ssfbin[0x710:0x720] = sndcmd([0x83, 0x00, effect])                 # EFFECT_CHANGE
    ssfbin[0x720:0x730] = sndcmd([0x05, 0x00, 0x00, volume, 0x00])       # SEQUENCE_VOLUME
    ssfbin[ssoffset:ssoffset + 0x10] = sndcmd([0x01, 0x00, 0x00, bank, track, 0x00])   # SEQUENCE_START
# -----------------------------------------------------------------------------------------------------
    # Read offsets from area map
    offset = 0x500
    while offset < 0x600:
        maptype = ssfbin[offset] >> 4
        mapbank = ssfbin[offset] & 0xF
        if ssfbin[offset] == 0xFF:
            break
        if mapbank == bank:
            if maptype == 0x00:
                abin = unpack('>I', ssfbin[offset:offset + 4].tobytes())[0] & 0x00FFFFFF
                aszbin = unpack('>I', ssfbin[offset + 4:offset + 8].tobytes())[0] & 0x00FFFFFF
            elif maptype == 0x01:
                aseq = unpack('>I', ssfbin[offset:offset + 4].tobytes())[0] & 0x00FFFFFF
                aszseq = unpack('>I', ssfbin[offset + 4:offset + 8].tobytes())[0] & 0x00FFFFFF
        if maptype == 0x02 and mapbank == effect:
            aexb = unpack('>I', ssfbin[offset:offset + 4].tobytes())[0] & 0x00FFFFFF
            aszexb = unpack('>I', ssfbin[offset + 4:offset + 8].tobytes())[0] & 0x00FFFFFF
        if maptype == 0x03:
            aram = unpack('>I', ssfbin[offset:offset + 4].tobytes())[0] & 0x00FFFFFF
            aszram = unpack('>I', ssfbin[offset + 4:offset + 8].tobytes())[0] & 0x00FFFFFF
            ssfbin[aram:aram + aszram] = array('B', [0x60, 0x00]) * (aszram // 2)
        offset += 0x8
# -----------------------------------------------------------------------------------------------------
    # Write tone data
    try:
        if szbin > aszbin:
            print('Warning [%s - bank 0x%02X]: Tone data overflows area map.' % (nout, bank))
        ssfbin[abin:abin + szbin] = databin
    except Exception:
        if nbin != '':
            print('Error [%s - bank 0x%02X]: Failed to write tone data.' % (nout, bank))
# -----------------------------------------------------------------------------------------------------
    # Write sequence data
    try:
        if szseq > aszseq:
            print('Warning [%s - bank 0x%02X]: Sequence data overflows area map.' % (nout, bank))
        ssfbin[aseq:aseq + szseq] = dataseq
    except Exception:
        if nseq != '':
            print('Error [%s - bank 0x%02X]: Failed to write sequence data.' % (nout, bank))
# -----------------------------------------------------------------------------------------------------
    # Write effect data
    try:
        if szexb > aszexb:
            print('Warning [%s - bank 0x%02X]: Effect data overflows area map.' % (nout, effect))
        ssfbin[aexb:aexb + szexb] = dataexb
    except Exception:
        if use_dsp:
            print('Error [%s - bank 0x%02X]: Failed to write effect data.' % (nout, effect))
    if use_dsp:
        try:
            aram
            if (aram & 0x1FFF) != 0:
                print('Error [%s - bank 0x%02X]: DSP RAM not aligned to 0x2000 offset.' % (nout, effect))
            reqram = (1 << (ssfbin[aexb + 0x20] + 14)) + 0x40
            if aszram < reqram:
                print('Error [%s - bank 0x%02X]: Not enough DSP RAM to support DSP program.' % (nout, effect))
        except Exception:
            print('Error [%s - bank 0x%02X]: No DSP RAM found.' % (nout, effect))
# -----------------------------------------------------------------------------------------------------
    if aseq:
        ntracks = ssfbin[aseq + 1]
    print('[%s - bank 0x%02X]: Sequence data contains %d track(s).' % (nout, bank, ntracks))
# -----------------------------------------------------------------------------------------------------
    # Write 2 output files
    # - ssfdata.bin contains load address and is inputted directly into bin2psf
    # - 68000ram.bin does not contain the load address and is useful for multi-pass runs of this script
    ntmp = os.path.join(os.path.dirname(nout), 'temp.bin')
    nram = os.path.join(os.path.dirname(nout), '68000ram.bin')
    with open(ntmp, 'wb') as fo1, open(nram, 'wb') as fo2:
        fo1.write(b'\x00' * 4)    # load address
        fo1.write(ssfbin.tobytes())
        fo2.write(ssfbin.tobytes())
# -----------------------------------------------------------------------------------------------------
# Create the ssf (or ssflib/minissfs) file
    (bout, xout) = fnoext(nout)
    (btmp, xtmp) = fnoext(ntmp)
    if bout[len(xout):] == '.ssflib':
        os.system('bin2psf ssflib 17 %s 2> %s' % (ntmp, os.devnull))
        if os.access(nout, os.F_OK):
            os.remove(nout)
        os.rename('%s.ssflib' % os.path.join(os.path.dirname(nout), xtmp), nout)
        for itrack in range(0, ntracks):
            with open(ntmp, 'wb') as fo:
                fo.write(pack('<I', 0x700))
                ssfbin[ssoffset + 0x3] = bank
                ssfbin[ssoffset + 0x4] = itrack
                fo.write(ssfbin[0x700:0x780].tobytes())
            os.system('bin2psf minissf 17 %s 2> %s' % (ntmp, os.devnull))
            os.system('psfpoint "-_lib=%s" %s.minissf > %s' % (bout, os.path.join(os.path.dirname(nout), xtmp), os.devnull))
            fname = '%s_%02d_%02d.minissf' % (os.path.join(os.path.dirname(nout), xout), bank, itrack)
            if os.access(fname, os.F_OK):
                os.remove(fname)
            os.rename('%s.minissf' % os.path.join(os.path.dirname(nout), xtmp), fname)
    else:
        os.system('bin2psf ssf 17 %s 2> %s' % (ntmp, os.devnull))
        if os.access(nout, os.F_OK):
            os.remove(nout)
        os.rename('%s.ssf' % os.path.join(os.path.dirname(nout), xtmp), nout)
    return ssfbin
# =====================================================================================================


def _parse_args():
    p = argparse.ArgumentParser(description='Create SSF files from components')
    p.add_argument('--ndrv', help='sound driver file', default=ndrv)
    p.add_argument('--nmap', help='sound area map file', default=nmap)
    p.add_argument('--nbin', help='tone data file', default=nbin)
    p.add_argument('--nseq', help='sequence data file', default=nseq)
    p.add_argument('--nexb', help='DSP program file', default=nexb)
    p.add_argument('--nout', help='output ssf filename', default=nout)
    p.add_argument('--bank', help='sequence bank (int, supports 0x hex)', default=bank)
    p.add_argument('--track', help='track number (int, supports 0x hex)', default=track)
    p.add_argument('--volume', help='volume (int)', default=volume)
    p.add_argument('--mixerbank', help='mixer bank (int)', default=mixerbank)
    p.add_argument('--mixern', help='mixer number (int)', default=mixern)
    p.add_argument('--effect', help='effect number (int)', default=effect)
    p.add_argument('--use-dsp', help='use dsp (0/1)', default=use_dsp)
    args = p.parse_args()
    # convert numeric values (allow hex)
    def toint(x):
        try:
            return int(x, 0)
        except Exception:
            return int(x)
    args.bank = toint(args.bank)
    args.track = toint(args.track)
    args.volume = toint(args.volume)
    args.mixerbank = toint(args.mixerbank)
    args.mixern = toint(args.mixern)
    args.effect = toint(args.effect)
    args.use_dsp = toint(args.use_dsp)
    return args


if __name__ == '__main__':
    args = _parse_args()
    ssfmake(args.nout, args.ndrv, args.nmap, args.nbin, args.nseq, args.nexb,
            args.bank, args.track, args.volume, args.mixerbank, args.mixern, args.effect, args.use_dsp)

# =====================================================================================================
# Update history:
# 08-10-12 (0.14) - Fixed a slight bug in zeroing-out DSP work RAM. Minor clean-ups.
# 08-05-28 (0.13) - Changed script to explicitly zero-out DSP work RAM, since older version of the
#     SDDRVS driver fail to do this. This will remove pops at the beginning of tracks.
# 07-12-20 (0.12) - Same fix as v0.11 but done in a way that actually works.
# 07-12-19 (0.11) - Fixed error that occurs when trying to print out number of tracks from a sequence bank
#     not specified in the area map.
# 07-11-22 (0.10) - Created new set of general area maps, supporting DSP program banks 1-7 and more DSP RAM
#     size options. Put in error messages for DSP RAM problems.
# 07-11-09 (0.09) - Fixed some mistakes in tone bank settings in the general area maps. Changed the ssfmake
#     function to return an array representing sound memory - sometimes useful for post-processing.
# 07-10-28 (0.08) - Changed minissf output to include all sound commands, not just the sequence bank and
#     track numbers.
# 07-10-19 (0.07) - Changed DSP RAM sizes in the area maps to account for the additional 0x40 bytes.
# 07-10-13 (0.06) - Now account for effect number when reading from area map.
# 07-10-12 (0.05) - Fixed the general area maps to handle banks 0-7 instead of just bank 0.
# 07-10-09 (0.04) - Fixed output file handling for other output directories. Cleaned up extraneous output. Gave
#     general area maps better names. Added another general area map when the DSP is not being used, 
#     providing lots of space for tone and sequence data.
# 07-10-08 (0.03) - Added ssflib/minissf support. Made the script more flexible by defining ssfmake as a 
#     function. Converted a lot of the previous struct usage to array for more speed.
# 07-10-06 (0.02) - Moved input file closing to the right place. What was there before messed up multi-pass
#     runs.
# 07-09-28 (0.01) - Added output to include number of tracks in selected sequence data. Added ability
#     to ignore data by specifying empty strings for filenames. Added dump of sound memory (without the
#     ssf load address) to support multi-pass usage.
# 07-09-25 (0.00) - Initial version.
# =====================================================================================================