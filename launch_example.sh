#!/bin/bash

OUT="/tmp/out"

mkdir -p "$OUT" && \
    cp *.png "$OUT" && \
    python3 calculator.py --data data.csv --template template01.tex --scores "$1".csv --debug_output "$OUT"/"$1".csv -o "$OUT"/"$1".tex && \
    cd "$OUT" && \
    pdflatex "$OUT"/"$1".tex
