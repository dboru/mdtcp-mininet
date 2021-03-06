# set term pdfcairo size 3,2 font "Helvetica, 22"
set term pdfcairo font "Helvetica, 22"
set xlabel "Time(secs)"
set ylabel "cwnd (pkts)" offset 1.5
set output "cwnd_last_ca.pdf"
set key top center


# set yrange [0:1.0]
set xrange [0:15.5]
# set multiplot layout 2,2
# set title "Flow completion size=90K subflow=8"
# set logscale x 10
# set grid
 # set xtics 5

plot "last_ca_sf1" using ($7-43.019887):11 w l lw 4 dashtype 1 lc rgb "black" t "MDTCP_{SF1}",\
"last_ca_sf2" using ($7-43.019887):11 w l lw 4 dashtype 1 lc rgb "green" t "MDTCP_{SF2}","last_ca_dctcp" using ($7-43.019887):11 w l lw 4 dashtype 1 lc rgb "blue" t "DCTCP"

