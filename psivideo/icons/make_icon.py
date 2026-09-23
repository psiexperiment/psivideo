# Generates main-icon.png and main-icon.ico. Run from anywhere:
#   python make_icon.py
#
# The frame, palette and output sizes come from psiapp.icons, shared with the
# other psi programs (pip install psiapp[icons]). Only the motif is drawn here:
# a camera seen head-on, where cftscal's icon has a chirp and noise-exp's has
# noise. It echoes the camera glyph `psivideo.display` draws over the video
# window, so the taskbar button and the window agree on what the program is.
#
# The body is a solid white shape rather than the white outline the other
# icons draw their motifs with: an outlined body sits inside the frame as a
# second white rectangle, and at 16x16 the two merge into a blur. Filling it
# leaves one white shape and one cornflowerblue lens, which survives the
# smallest size in ICO_SIZES.
from pathlib import Path

from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

from psiapp.icons import FILL, FOREGROUND, make_icon


HERE = Path(__file__).parent

#: Corner radius of the camera body, in data units. Enough to look moulded
#: without reading as the rounded corner of a button.
CORNER_RADIUS = 2

#: Radius of the lens, in data units. Large enough to hold its color at
#: 16x16, small enough to keep a clear white margin around it.
LENS_RADIUS = 4.2


def draw(ax):
    # The body, and the viewfinder hood overlapping its top edge. Both are
    # filled with no edge, so they merge into a single silhouette.
    body = FancyBboxPatch(
        (-9, -8), 18, 14,
        boxstyle=f'round,pad=0,rounding_size={CORNER_RADIUS}',
        facecolor=FOREGROUND, edgecolor='none', zorder=4)
    ax.add_patch(body)

    hood = Rectangle((-7.5, 5), 5, 3.5, facecolor=FOREGROUND,
                     edgecolor='none', zorder=4)
    ax.add_patch(hood)

    # The lens, in the same color as the areas the signal icons fill.
    lens = Circle((0, -1), radius=LENS_RADIUS, facecolor=FILL,
                  edgecolor='none', zorder=5)
    ax.add_patch(lens)


if __name__ == '__main__':
    # Centered on the camera, with enough room that the body stays clear of
    # the frame. Both ranges are the same length so the lens comes out round.
    make_icon(draw, HERE / 'main-icon.png', HERE / 'main-icon.ico',
              xlim=(-14, 14), ylim=(-14, 14))
