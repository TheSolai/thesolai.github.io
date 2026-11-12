#!/bin/bash
# crop.sh <in> <out> <x> <y> <w> <h> [scale]
# sips --cropOffset is relative to the CENTER crop, so convert.
IN=$1; OUT=$2; X=$3; Y=$4; W=$5; H=$6; S=${7:-0}
CW=$(sips -g pixelWidth "$IN" | awk '/pixelWidth/{print $2}')
CH=$(sips -g pixelHeight "$IN" | awk '/pixelHeight/{print $2}')
BASEY=$(( (CH - H) / 2 ))
BASEX=$(( (CW - W) / 2 ))
DY=$(( Y - BASEY ))
DX=$(( X - BASEX ))
sips -c $H $W --cropOffset $DY $DX "$IN" --out "$OUT" >/dev/null 2>&1
if [ "$S" != "0" ]; then sips -Z $S "$OUT" --out "$OUT" >/dev/null 2>&1; fi
echo "$OUT $(sips -g pixelWidth -g pixelHeight "$OUT" | awk '/pixel/{print $2}' | tr '\n' ' ')"
