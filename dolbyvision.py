# -*- coding: utf-8 -*-
# Module: PyDolbyVision
# Created on: 14/04/2023
# Authors: -∞WKS∞-#3982
# Version: 1.0.0

import argparse
import os

import ffmpeg

import dolby_vision


def create_dolby_vision_track(input_file, profile_number):
    dv_profile = dolby_vision.get_profile(profile_number)

    if dv_profile is None:
        raise ValueError(f"Invalid Dolby Vision profile: {profile_number}")

    dv_data = dolby_vision.generate_data(input_file, dv_profile)
    dv_track = ffmpeg.input("pipe:").video.filter("dolby_vision", dv_data=dv_data)

    return dv_track


def create_video_track(input_file, dolby_vision_profile=None, bitrate=None):
    if dolby_vision_profile is not None:
        dv_profile = dolby_vision.get_profile(dolby_vision_profile)

        if dv_profile is None:
            raise ValueError(f"Invalid Dolby Vision profile: {dolby_vision_profile}")

        dolby_vision_data = dolby_vision.generate_data(input_file, dv_profile)
    else:
        dolby_vision_data = None

    video = ffmpeg.input(input_file).video
    if dolby_vision_data is not None:
        video = video.filter("dolby_vision", dv_data=dolby_vision_data)

    if bitrate is not None:
        video = video.bitrate(bitrate)

    return video


def main():
    parser = argparse.ArgumentParser(description="Convert video to Dolby Vision-compatible format")
    parser.add_argument("--input", type=str, required=True, help="Input video file path")
    parser.add_argument("--output", type=str, required=True, help="Output video file path")
    parser.add_argument("--dolby-vision-profile", type=str, default="5",
                        help="Dolby Vision profile (4, 5, or 8)")
    parser.add_argument("--bitrate", type=int, default=768,
                        help="Bitrate of the output video (in kb/s)")
    parser.add_argument("--frame-rate", type=float, help="Frame rate of the output video")
    parser.add_argument("--audio-bitrate", type=int, help="Bitrate of the output audio (in kb/s)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Input file '{args.input}' does not exist.")
        return

    video = create_video_track(args.input, args.dolby_vision_profile, args.bitrate)
    audio = ffmpeg.input(args.input).audio.copy()

    if args.audio_bitrate is not None:
        audio = audio.filter("aformat", "sample_fmts=fltp:channel_layouts=stereo")
        audio = audio.filter("asetrate", "48000")
        audio = audio.filter("abitrat", f"{args.audio_bitrate}k")

    if args.frame_rate is not None:
        video = video.filter("fps", args.frame_rate, round="up")

    output = ffmpeg.output(video, audio, args.output, vcodec="libx265", pix_fmt="yuv420p10le",
                           x265_params="colorprim=bt2020:transfer=smpte2084:colormatrix=bt2020nc",
                           preset="slow", crf=18, tune="fastdecode", movflags="+faststart")

    ffmpeg.run(output, input_data=None, capture_stdout=False, capture_stderr=True,
               quiet=False, overwrite_output=True)

if __name__ == "__main__":
    main()
