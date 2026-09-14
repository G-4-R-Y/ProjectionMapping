from __future__ import annotations

import argparse


def _show_frames(frames, display: int, hold_ms: int):
    import cv2
    name = "ProjectionMapping"
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    if display > 0:
        cv2.moveWindow(name, display * 1920, 0)
    for frame in frames:
        image = frame.image if hasattr(frame, "image") else frame
        cv2.imshow(name, image)
        if (cv2.waitKey(hold_ms) & 0xFF) == 27:
            break
    cv2.destroyWindow(name)


def cmd_patterns(args):
    from .patterns import checkerboard, color_ramp, graycode_sequence, grid, phase_shift_sequence, PatternFrame
    if args.kind == "checkerboard":
        frames = [PatternFrame(checkerboard(args.width, args.height), "checkerboard", {})]
    elif args.kind == "grid":
        frames = [PatternFrame(grid(args.width, args.height), "grid", {})]
    elif args.kind == "ramp":
        frames = [PatternFrame(color_ramp(args.width, args.height), "ramp", {})]
    elif args.kind == "graycode":
        frames = graycode_sequence(args.width, args.height)
    else:
        frames = phase_shift_sequence(args.width, args.height)
    _show_frames(frames, args.display, args.hold_ms)


def cmd_camera(args):
    import cv2
    from .capture import Camera
    with Camera(args.device) as cam:
        while True:
            frame = cam.read()
            cv2.imshow("camera", frame)
            if (cv2.waitKey(1) & 0xFF) == 27:
                break
    cv2.destroyAllWindows()


def build_parser():
    p = argparse.ArgumentParser(prog="projection-map")
    sub = p.add_subparsers(required=True)
    pp = sub.add_parser("patterns")
    pp.add_argument("--kind", choices=["checkerboard", "grid", "ramp", "graycode", "phase"], default="grid")
    pp.add_argument("--width", type=int, default=1920)
    pp.add_argument("--height", type=int, default=1080)
    pp.add_argument("--display", type=int, default=1)
    pp.add_argument("--hold-ms", type=int, default=1000)
    pp.set_defaults(func=cmd_patterns)
    pc = sub.add_parser("camera")
    pc.add_argument("--device", type=int, default=0)
    pc.set_defaults(func=cmd_camera)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
