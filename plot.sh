# set term pdfcairo size 3,2 font "Helvetica, 22"
set term pdfcairo font "Helvetica, 22"
set xlabel "Flow completion time (ms)"
set ylabel "CWND" offset 1.5
set output "fct_shortlong.pdf"
set key center right
#set key at 200,270

# set xrange [0:3.0]

# stats "fct_ndp_perm_iter1" using 6 name "ndp1"
stats "dctcp_shortlong_fct" using 3 name "dctcp"
stats "mtcp_shortlong_fct" using 3 name "mtcp"
stats "mdctcp_shortlong_fct" using 3 name "mdtcp"
stats "ndp_shortlong_fct" using 3 name "ndp"


# set yrange [0:1.0]
# set xrange [0:10]
# set multiplot layout 2,2
# set title "Flow completion size=90K subflow=8"
set logscale x 10
set grid
 # set xtics 5

plot "dctcp_shortlong_fct" using 3:(1./dctcp_records) smooth cumulative w l lw 4 dashtype 1 lc rgb "black" t "DCTCP",\
"mdctcp_shortlong_fct" using 3:(1./mdtcp_records) smooth cumulative w l lw 4 dashtype 1 lc rgb "green" t "MDTCP",\
"mtcp_shortlong_fct" using 3:(1./mtcp_records) smooth cumulative w l lw 4 dashtype 1 lc rgb "blue" t "MPTCP",\
"ndp_shortlong_fct" using 3:(1./ndp_records) smooth cumulative w l lw 4 dashtype 1 lc rgb "red" t "NDP"

