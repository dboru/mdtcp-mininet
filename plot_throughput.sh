# set term pdfcairo size 3,2 font "Helvetica, 22"
set term pdfcairo font "Helvetica, 22"
set xlabel "Time (secs)"
set ylabel "Throughput[Mb/s]" offset 1.5
set output "throughput1sf.pdf"
set key center right



# set yrange [0:1.0]
# set xrange [0:10]
# set multiplot layout 2,2
# set title "Flow completion size=90K subflow=8"

set grid
 # set xtics 5

plot "iperf_bandwith_dctcp_log.txt" using 8 w l lw 4 dashtype 1 lc rgb "black" t "DCTCP",\
"iperf_bandwith_mdtcp_log.txt" using 8 w l lw 4 dashtype 1 lc rgb "green" t "MDTCP(1SF)"

