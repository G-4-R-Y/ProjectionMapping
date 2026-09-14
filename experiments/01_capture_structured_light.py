"""Project Gray-code patterns and save synchronized camera captures.

Run on the machine connected to the projector. ESC aborts.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import cv2
from projection_mapping.capture import Camera
from projection_mapping.patterns import graycode_sequence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--projector-width', type=int, default=1920)
    ap.add_argument('--projector-height', type=int, default=1080)
    ap.add_argument('--camera', type=int, default=0)
    ap.add_argument('--display', type=int, default=1)
    ap.add_argument('--settle-ms', type=int, default=180)
    ap.add_argument('--output', default='calibration_data/graycode')
    args = ap.parse_args()

    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    frames = graycode_sequence(args.projector_width, args.projector_height, include_inverse=True)
    name = 'projector'
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    if args.display > 0:
        cv2.moveWindow(name, args.display * args.projector_width, 0)

    manifest = []
    with Camera(args.camera) as cam:
        for i, pat in enumerate(frames):
            cv2.imshow(name, pat.image)
            cv2.waitKey(1)
            time.sleep(args.settle_ms / 1000)
            captured = cam.read()
            filename = f'{i:04d}_{pat.name}.png'
            cv2.imwrite(str(out / filename), captured)
            manifest.append({'file': filename, **pat.metadata, 'name': pat.name})
            print(f'[{i+1}/{len(frames)}] {filename}')
    (out / 'manifest.json').write_text(json.dumps({'projector': [args.projector_width, args.projector_height], 'frames': manifest}, indent=2))
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
