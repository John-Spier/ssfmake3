# ssfmake3

A Python 3 tool for creating SSF (Sega Sound Format) files from individual components. This script combines sound drivers, area maps, tone data, sequence data, and DSP programs into playable SSF audio files.

## Overview

SSF is a video game music format used primarily for Sega Saturn games. This tool automates the process of assembling the various binary components required to create a complete SSF file.

## Requirements

- Python 3.x
- `bin2psf` - PSF creation tool (must be in system PATH or current directory)
- `psfpoint` - PSF manipulation tool (required for ssflib/minissf creation)

These external tools are part of the psf2 utilities suite and must be installed separately.

## Installation

1. Clone or download this repository
2. Ensure Python 3 is installed
3. Install the required psf2 utilities (`bin2psf` and `psfpoint`)

## Usage

### Basic Command

```bash
python ssfmake3.py [options]
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--ndrv` | (empty) | Sound driver file path |
| `--nmap` | (empty) | Sound area map file path |
| `--nbin` | (empty) | Tone data file path |
| `--nseq` | (empty) | Sequence data file path |
| `--nexb` | (empty) | DSP program file path |
| `--nout` | `ssfdata.ssf` | Output filename (`.ssf`, `.ssflib`, or `.minissf`) |
| `--bank` | `0x00` | Sequence bank number (decimal or hex, e.g., `0x05`) |
| `--track` | `0x00` | Sequence track number (decimal or hex) |
| `--volume` | `0x7F` | Volume level (0x00-0x7F; reduce if clipping) |
| `--mixerbank` | `0x00` | Mixer bank number (usually same as `--bank`) |
| `--mixern` | `0x00` | Mixer number (usually 0) |
| `--effect` | `0x00` | Effect number (usually 0) |
| `--use-dsp` | `1` | Enable DSP (1 = enabled, 0 = disabled) |

### Examples

#### Create a basic SSF file

```bash
python ssfmake3.py \
  --ndrv driver.bin \
  --nmap areamap.bin \
  --nbin tones.bin \
  --nseq sequence.bin \
  --nout output.ssf
```

#### Create an SSF with DSP effects

```bash
python ssfmake3.py \
  --ndrv driver.bin \
  --nmap areamap.bin \
  --nbin tones.bin \
  --nseq sequence.bin \
  --nexb dsp_program.bin \
  --effect 1 \
  --use-dsp 1 \
  --nout output.ssf
```

#### Create a multi-track SSFLIB with minissfs

```bash
python ssfmake3.py \
  --ndrv driver.bin \
  --nmap areamap.bin \
  --nbin tones.bin \
  --nseq sequence.bin \
  --bank 0x02 \
  --nout output.ssflib
```

When the output filename ends with `.ssflib`, the script will:
1. Create a main `.ssflib` file
2. Generate individual `.minissf` files for each track in the specified sequence bank

#### Using hexadecimal values

All numeric parameters support both decimal and hexadecimal notation:

```bash
python ssfmake3.py \
  --ndrv driver.bin \
  --nmap areamap.bin \
  --nbin tones.bin \
  --nseq sequence.bin \
  --bank 0x05 \
  --track 0x03 \
  --volume 127 \
  --nout output.ssf
```

## Output Files

The script generates the following output files:

- **Primary Output**: The specified SSF file (`.ssf`, `.ssflib`, or `.minissf`)
- **Intermediate Files**: 
  - `temp.bin` - Binary with load address (used by bin2psf)
  - `68000ram.bin` - Binary without load address (useful for multi-pass runs)

Note: Intermediate files are created in the same directory as the output file.

## Parameters Explained

### Bank and Track Selection

- **`--bank`**: Selects which sequence bank to use from the sequence data file. Banks are usually numbered 0-7.
- **`--track`**: Selects which track within the chosen bank to play.

### Mixer Configuration

- **`--mixerbank`**: Specifies which mixer bank to use. Usually matches `--bank`.
- **`--mixern`**: Specifies which mixer within the bank. Usually 0.

### DSP (Digital Signal Processing)

- **`--nexb`**: Path to a DSP program file (required to use DSP effects)
- **`--effect`**: Effect number to use with the DSP program
- **`--use-dsp`**: Set to 1 to enable DSP, 0 to disable

If a DSP file is not specified or is empty, DSP will be automatically disabled regardless of `--use-dsp` setting.

### Volume Control

- **`--volume`**: Audio volume level (0x00 = silent, 0x7F = maximum). Reduce if audio clipping occurs.

## Output Format Selection

The output format is determined by the file extension of `--nout`:

- **`.ssf`** - Single SSF file containing the specified track
- **`.ssflib`** - SSF library file with individual minissf files for each track in the bank
- **`.minissf`** - Single minissf file (for standalone track playback)

## Error Handling

The script will display warnings and errors for common issues:

- **Data overflow**: When tone or sequence data exceeds the allocated memory area
- **DSP RAM issues**: When DSP RAM is not properly aligned or insufficient
- **Missing data**: When required sequence or tone data cannot be found

## Notes

- Use empty strings (omit the parameter) if a particular file type isn't needed
- The area map defines memory layout for the various data sections
- This script is useful for batch processing or scripting SSF creation workflows
- Output can be used directly with psf2 or compatible players

## References

- Original script version 0.14 (2008-10-12) by kingshriek
- Converted to Python 3 with command-line interface
- Based on Sega Saturn sound format specifications

## License

See repository for license information.