#!/bin/bash

# Note: Mininet must be run as root.  So invoke this shell script
# using sudo.

mn -c 

bw_sender=20
bw_receiver=20
delay='0.25ms'
redmin=10000
redmax=10001
redprob=1.0
redlimit=100000
redavpkt=1500
redburst=11

iperf_port=5001

# modprobe tcp_probe for cwnd and related stats
modprobe tcp_probe
#remove previous capture files
rm dctcp_cap.txt mdtcp_cap.txt
for qsize in 200; do
    dirResult=results

    # Expt 1 : Queue occupancy over time - comparing DCTCP & TCP
    dir1=mdtcp-q$qsize
    time=15
    # dir2=tcp-q$qsize
    #Make directories for TCP, DCTCP and the comparison graph
    mkdir $dir1 $dir2 $dirResult 2>/dev/null
    # Measure queue occupancy with DCTCP
    python mdtcp.py --bw-sender $bw_sender \
                    --bw-receiver $bw_receiver \
                    --delay $delay \
                    --dir $dir1 \
                    --maxq $qsize \
                    --time $time \
                    --n 4 \
                    --enable-ecn 1 \
                    --enable-red 1 \
                    --enable-mdtcp 1 \
                    --expt 1\
                    --intf $2\
                    --redmin $redmin \
                    --redmax $redmax \
                    --redlimit $redlimit \
                    --redprob  $redprob  \
                    --redburst $redburst \
                    --redavpkt $redavpkt
done
