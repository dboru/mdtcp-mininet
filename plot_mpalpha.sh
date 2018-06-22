# set term pdfcairo size 3,2 font "Helvetica, 22"
set term pdfcairo font "Helvetica, 22"
set xlabel "Time(secs)"
set ylabel "Multipath alpha" offset 1.5
set output "mpalpha.pdf"
set key top center


# set yrange [0:1.0]
set xrange [0:15.5]
# set multiplot layout 2,2
# set title "Flow completion size=90K subflow=8"
# set logscale x 10
# set grid
 # set xtics 5

plot "mpalpha1" using ($7-42.991234):($9/1024) w l lw 4 dashtype 1 lc rgb "black" t "MDTCP_{SF1}",\
"mpalpha2" using ($7-42.991234):($9/1024) w l lw 4 dashtype 1 lc rgb "green" t "MDTCP_{SF2}","mpalphadc" using ($7-42.991234):($9/1024) w l lw 4 dashtype 1 lc rgb "blue" t "DCTCP"

