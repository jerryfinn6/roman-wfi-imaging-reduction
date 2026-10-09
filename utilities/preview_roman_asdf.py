"""Run in the roman environment: python preview_roman_asdf.py INPUT.asdf"""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from astropy.visualization import ImageNormalize, AsinhStretch
from astropy.io import fits
import roman_datamodels as rdm

parser = argparse.ArgumentParser()
parser.add_argument('input', type=Path)
parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)
with rdm.open(args.input) as model:
    data = np.asarray(model.data)
    print('Model:', type(model).__name__, 'Shape:', data.shape, 'Dtype:', data.dtype)
    image = data[-1].copy() if data.ndim == 3 else data.copy()
    print('Finite pixels:', np.isfinite(image).sum(), '/', image.size)
    sample = image[::4, ::4]
    lo, hi = np.nanpercentile(sample, [1, 99.5])
    print('Display limits:', lo, hi)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), layout='constrained')
    norm = ImageNormalize(vmin=lo, vmax=hi, stretch=AsinhStretch())
    axes[0].imshow(image, origin='lower', cmap='gray', norm=norm, interpolation='nearest')
    axes[0].set_title('Full detector')
    y, x = image.shape
    half = 256
    axes[1].imshow(image[y//2-half:y//2+half, x//2-half:x//2+half], origin='lower', cmap='gray', norm=norm,
                   extent=(x//2-half,x//2+half,y//2-half,y//2+half), interpolation='nearest')
    axes[1].set_title('Central 512 × 512 pixels')
    for ax in axes:
        ax.set_xlabel('Detector x (pixels)')
        ax.set_ylabel('Detector y (pixels)')
    fig.suptitle(args.input.stem + (' — last resultant' if data.ndim == 3 else ' — calibrated image'), fontsize=10)
    png = args.output_dir / (args.input.stem + '_preview.png')
    fig.savefig(png, dpi=160)
    plt.close(fig)
    out = args.output_dir / (args.input.stem + '_preview.fits')
    hdu = fits.PrimaryHDU(image)
    hdu.header['COMMENT'] = 'Pixel-only preview. Original ASDF retains WCS, DQ, and metadata.'
    hdu.writeto(out, overwrite=True)
    print('Saved:', png, out, sep='\n')
