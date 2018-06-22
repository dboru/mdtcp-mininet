#!/bin/bash
# set term pdfcairo size 3,2 font "Helvetica, 22"
set term pdfcairo font "Helvetica, 22"
set xlabel "Time (secs)"
set ylabel "Queue (Pkts)" offset 1.5
set output "queue.pdf"
set key top right


# set yrange [0:1.0]
# set xrange [0:15.5]
# set multiplot layout 2,2
# set title "Flow completion size=90K subflow=8"
# set logscale x 10
# set grid
 # set xtics 5

plot "q.txt" using ($1-1529498874.148126):2 w l lw 4 lc rgb "red"

